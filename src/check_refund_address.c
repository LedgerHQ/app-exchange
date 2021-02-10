#include "check_refund_address.h"
#include "os.h"
#include "currency_lib_calls.h"
#include "globals.h"
#include "swap_errors.h"
#include "reply_error.h"
#include "parse_check_address_message.h"
#include "menu.h"
#include "parse_coin_config.h"

int check_refund_address(rate_e P1,
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
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    static unsigned char hash[CURVE_SIZE_BYTES];

    os_memset(hash, 0, sizeof(hash));

    cx_hash_sha256(config.bytes, config.size, hash, CURVE_SIZE_BYTES);

    if (cx_ecdsa_verify(&ctx->ledger_public_key,
                        CX_LAST,
                        CX_SHA256,
                        hash,
                        CURVE_SIZE_BYTES,
                        der.bytes,
                        der.size) == 0) {
        PRINTF("Error: Fail to verify signature of coin config");

        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }

    if (parse_coin_config(&config,            //
                          &ticker,            //
                          &application_name,  //
                          &ctx->payin_coin_config) == 0) {
        PRINTF("Error: Can't parse refund coin config command\n");

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
    if (strlen(ctx->received_transaction.currency_from) != ticker.size ||
        strncmp(ctx->received_transaction.currency_from,  //
                (const char *) ticker.bytes,              //
                ticker.size) != 0) {
        PRINTF("Error: Refund ticker doesn't match configuration ticker\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    // creating 0-terminated application name
    os_memset(ctx->payin_binary_name, 0, sizeof(ctx->payin_binary_name));
    os_memcpy(ctx->payin_binary_name, application_name.bytes, application_name.size);

    // check address
    if (check_address(&ctx->payin_coin_config,
                      &address_parameters,
                      ctx->payin_binary_name,
                      ctx->received_transaction.refund_address,
                      ctx->received_transaction.refund_extra_id) != 1) {
        PRINTF("Error: Refund address validation failed");

        return reply_error(ctx, INVALID_ADDRESS, send);
    }

    static char printable_send_amount[PRINTABLE_AMOUNT_SIZE];
    os_memset(printable_send_amount, 0, sizeof(printable_send_amount));

    if (get_printable_amount(&ctx->payin_coin_config,
                             ctx->payin_binary_name,
                             ctx->received_transaction.amount_to_provider.bytes,
                             ctx->received_transaction.amount_to_provider.size,
                             printable_send_amount,
                             sizeof(printable_send_amount),
                             false) < 0) {
        PRINTF("Error: Failed to get source currency printable amount");

        return reply_error(ctx, INTERNAL_ERROR, send);
    }
    PRINTF("Send amount: %s\n", printable_send_amount);

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
    PRINTF("Fees: %s\n", printable_fees_amount);

    ctx->state = WAITING_USER_VALIDATION;

    ui_validate_amounts(P1,  //
                        P2,
                        ctx,                    //
                        printable_send_amount,  //
                        printable_fees_amount,  //
                        send);

    return 0;
}
