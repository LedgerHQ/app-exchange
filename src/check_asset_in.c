#include "check_asset_in.h"
#include "os.h"
#include "swap_errors.h"
#include "globals.h"
#include "currency_lib_calls.h"
#include "reply_error.h"
#include "parse_check_address_message.h"
#include "parse_coin_config.h"
#include "printable_amount.h"
#include "menu.h"

int check_asset_in(rate_e P1,
                   subcommand_e P2,
                   swap_app_context_t *ctx,
                   const buf_t *input,
                   SendFunction send) {
    static buf_t config;
    static buf_t der;
    static buf_t address_parameters;
    static buf_t ticker;
    static buf_t application_name;

    if (parse_check_address_message(input, &config, &der, &address_parameters) == 0) {
        PRINTF("Error: Can't parse CHECK_ASSET_IN command\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    static unsigned char hash[CURVE_SIZE_BYTES];

    cx_hash_sha256(config.bytes, config.size, hash, CURVE_SIZE_BYTES);

    if (cx_ecdsa_verify(&ctx->ledger_public_key,
                        CX_LAST,
                        CX_SHA256,
                        hash,
                        CURVE_SIZE_BYTES,
                        der.bytes,
                        der.size) == 0) {
        PRINTF("Error: Fail to verify signature of coin config\n");

        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }

    if (parse_coin_config(&config, &ticker, &application_name, &config) == 0) {
        PRINTF("Error: Can't parse payout coin config command\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    if (ticker.size < 2 || ticker.size > 9) {
        PRINTF("Error: Ticker length should be in [3, 9]\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    if (application_name.size < 3 || application_name.size > 15) {
        PRINTF("Error: Application name should be in [3, 15]\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    // Check that given ticker match current context
    if (strlen(ctx->sell_transaction.in_currency) != ticker.size ||
        strncmp(ctx->sell_transaction.in_currency, (const char *) ticker.bytes, ticker.size) != 0) {
        PRINTF("Error: Payout ticker doesn't match configuration ticker\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    PRINTF("Coin config parsed OK\n");

    // creating 0-terminated application name
    os_memset(ctx->payin_binary_name, 0, sizeof(ctx->payin_binary_name));
    os_memcpy(ctx->payin_binary_name, application_name.bytes, application_name.size);

    PRINTF("PATH inside the SWAP = %.*H\n", address_parameters.size, address_parameters.bytes);

    static char in_printable_amount[PRINTABLE_AMOUNT_SIZE];

    // getting printable amount
    if (get_printable_amount(&config,
                             ctx->payin_binary_name,
                             ctx->sell_transaction.in_amount.bytes,
                             ctx->sell_transaction.in_amount.size,
                             in_printable_amount,
                             sizeof(in_printable_amount),
                             false) < 0) {
        PRINTF("Error: Failed to get destination currency printable amount\n");

        return reply_error(ctx, INTERNAL_ERROR, send);
    }

    PRINTF("Amount = %s\n", in_printable_amount);

    static char printable_fees_amount[PRINTABLE_AMOUNT_SIZE];
    os_memset(printable_fees_amount, 0, sizeof(printable_fees_amount));

    if (get_printable_amount(&ctx->payin_coin_config,
                             ctx->payin_binary_name,
                             ctx->transaction_fee,
                             ctx->transaction_fee_length,
                             printable_fees_amount,
                             sizeof(printable_fees_amount),
                             true) < 0) {
        PRINTF("Error: Failed to get source currency fees amount");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }

    size_t len = strlen(ctx->sell_transaction.out_currency);
    if (len + 1 >= sizeof(ctx->printable_get_amount)) {
        return reply_error(ctx, INTERNAL_ERROR, send);
    }

    strncpy(ctx->printable_get_amount,
            ctx->sell_transaction.out_currency,
            sizeof(ctx->printable_get_amount));
    ctx->printable_get_amount[len] = ' ';
    ctx->printable_get_amount[len + 1] = '\x00';

    if (get_fiat_printable_amount(ctx->sell_transaction.out_amount.coefficient.bytes,
                                  ctx->sell_transaction.out_amount.coefficient.size,
                                  ctx->sell_transaction.out_amount.exponent,
                                  ctx->printable_get_amount + len + 1,
                                  sizeof(ctx->printable_get_amount) - (len + 1)) < 0) {
        PRINTF("Error: Failed to get source currency printable amount\n");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }

    PRINTF("%s\n", ctx->printable_get_amount);

    ctx->state = WAITING_USER_VALIDATION;

    ui_validate_amounts(P1,  //
                        P2,
                        ctx,                    //
                        in_printable_amount,    //
                        printable_fees_amount,  //
                        send);

    return 0;
}
