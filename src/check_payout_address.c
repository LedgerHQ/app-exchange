#include <os.h>
#include <cx.h>

#include "check_payout_address.h"
#include "swap_errors.h"
#include "globals.h"
#include "currency_lib_calls.h"
#include "reply_error.h"
#include "parse_check_address_message.h"
#include "parse_coin_config.h"
#include "printable_amount.h"
#include "menu.h"
#include "checks.h"

int check_payout_address(swap_app_context_t *ctx, const command_t *cmd, SendFunction send) {
    static buf_t config;
    static buf_t der;
    static buf_t address_parameters;
    static buf_t ticker;
    static buf_t application_name;

    if (parse_check_address_message(cmd, &config, &der, &address_parameters) == 0) {
        PRINTF("Error: Can't parse CHECK_PAYOUT_ADDRESS command\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    PRINTF("CHECK_PAYOUT_ADDRESS parsed OK\n");

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

    if (!check_ticker_length(&ticker)) {
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    if (!check_app_name_length(&application_name)) {
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    // Check that given ticker match current context
    if (strlen(ctx->received_transaction.currency_to) != ticker.size ||
        strncmp(ctx->received_transaction.currency_to, (const char *) ticker.bytes, ticker.size) !=
            0) {
        PRINTF("Error: Payout ticker '%s' doesn't match configuration ticker '%s'\n",
               ticker.bytes,
               ctx->received_transaction.currency_to);

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    PRINTF("Coin config parsed OK\n");

    // creating 0-terminated application name
    memset(ctx->payin_binary_name, 0, sizeof(ctx->payin_binary_name));
    memcpy(ctx->payin_binary_name, application_name.bytes, application_name.size);

    PRINTF("PATH inside the SWAP = %.*H\n", address_parameters.size, address_parameters.bytes);

    // check address
    if (check_address(&config,
                      &address_parameters,
                      ctx->payin_binary_name,
                      ctx->received_transaction.payout_address,
                      ctx->received_transaction.payout_extra_id) != 1) {
        PRINTF("Error: Payout address validation failed\n");

        return reply_error(ctx, INVALID_ADDRESS, send);
    }

    PRINTF("Payout address is OK\n");

    // getting printable amount
    if (get_printable_amount(&config,
                             ctx->payin_binary_name,
                             ctx->received_transaction.amount_to_wallet.bytes,
                             ctx->received_transaction.amount_to_wallet.size,
                             ctx->printable_get_amount,
                             sizeof(ctx->printable_get_amount),
                             false) < 0) {
        PRINTF("Error: Failed to get destination currency printable amount\n");

        return reply_error(ctx, INTERNAL_ERROR, send);
    }

    PRINTF("Amount = %s\n", ctx->printable_get_amount);

    unsigned char output_buffer[2] = {0x90, 0x00};

    if (send(output_buffer, 2) < 0) {
        PRINTF("Error: failed to send\n");

        return -1;
    }

    ctx->state = TO_ADDR_CHECKED;

    return 0;
}
