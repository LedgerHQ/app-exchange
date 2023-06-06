#include <os.h>
#include <cx.h>

#include "check_refund_address.h"
#include "currency_lib_calls.h"
#include "globals.h"
#include "swap_errors.h"
#include "reply_error.h"
#include "parse_check_address_message.h"
#include "menu.h"
#include "process_transaction.h"
#include "parse_coin_config.h"

// Check if a given ticker matches the current swap context
static bool check_matching_ticker(swap_app_context_t *ctx, const buf_t *ticker) {
    char normalized_ticker_name[9];
    uint8_t normalized_ticker_len;

    // Normalize the ticker name first
    memcpy(normalized_ticker_name, ticker->bytes, sizeof(normalized_ticker_name));
    normalized_ticker_name[ticker->size] = '\0';
    to_uppercase(normalized_ticker_name, ticker->size);
    set_ledger_currency_name(normalized_ticker_name, sizeof(normalized_ticker_name));
    // Recalculate length in case it changed
    normalized_ticker_len = strlen(normalized_ticker_name);

    if (strncmp(normalized_ticker_name,
                (const char *) ticker->bytes,
                MAX(normalized_ticker_len, ticker->size)) != 0) {
        PRINTF("Normalized ticker, from '%.*s' to '%s'\n",
               ticker->size,
               ticker->bytes,
               normalized_ticker_name);
    }

    if (strlen(ctx->received_transaction.currency_from) != normalized_ticker_len ||
        strncmp(ctx->received_transaction.currency_from,
                normalized_ticker_name,
                normalized_ticker_len) != 0) {
        PRINTF("Error: Refund ticker '%.*s' doesn't match expected ticker '%.*s'\n",
               normalized_ticker_len,
               normalized_ticker_name,
               strlen(ctx->received_transaction.currency_from),
               ctx->received_transaction.currency_from);
        return false;
    }

    return true;
}

int check_refund_address(swap_app_context_t *ctx, const command_t *cmd, SendFunction send) {
    static buf_t config;
    static buf_t der;
    static buf_t address_parameters;
    static buf_t ticker;
    static buf_t application_name;

    if (parse_check_address_message(cmd, &config, &der, &address_parameters) == 0) {
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    static unsigned char hash[CURVE_SIZE_BYTES];

    memset(hash, 0, sizeof(hash));

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

    if (parse_coin_config(&config, &ticker, &application_name, &ctx->payin_coin_config) == 0) {
        PRINTF("Error: Can't parse refund coin config command\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    if (ticker.size < 2 || ticker.size > 9) {
        PRINTF("Error: Ticker length should be in [3, 9]\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    if (application_name.size < 3 || application_name.size > BOLOS_APPNAME_MAX_SIZE_B) {
        PRINTF("Error: Application name should be in [3, BOLOS_APPNAME_MAX_SIZE_B]\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    // Check that refund ticker matches the current context
    if (!check_matching_ticker(ctx, &ticker)) {
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    // creating 0-terminated application name
    memset(ctx->payin_binary_name, 0, sizeof(ctx->payin_binary_name));
    memcpy(ctx->payin_binary_name, PIC(application_name.bytes), application_name.size);

    // check address
    if (check_address(&ctx->payin_coin_config,
                      &address_parameters,
                      ctx->payin_binary_name,
                      ctx->received_transaction.refund_address,
                      ctx->received_transaction.refund_extra_id) != 1) {
        PRINTF("Error: Refund address validation failed");

        return reply_error(ctx, INVALID_ADDRESS, send);
    }

    static char printable_send_amount[MAX_PRINTABLE_AMOUNT_SIZE];
    memset(printable_send_amount, 0, sizeof(printable_send_amount));

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

    static char printable_fees_amount[MAX_PRINTABLE_AMOUNT_SIZE];
    memset(printable_fees_amount, 0, sizeof(printable_fees_amount));

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

    ui_validate_amounts(cmd->rate,  //
                        cmd->subcommand,
                        ctx,                    //
                        printable_send_amount,  //
                        printable_fees_amount,  //
                        send);

    return 0;
}
