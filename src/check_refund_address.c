#include <os.h>
#include <cx.h>

#include "check_refund_address.h"
#include "currency_lib_calls.h"
#include "globals.h"
#include "swap_errors.h"
#include "io.h"
#include "parse_check_address_message.h"
#include "menu.h"
#include "validate_transaction.h"
#include "process_transaction.h"
#include "parse_coin_config.h"

// Check if a given ticker matches the current swap context
static bool check_matching_ticker(const buf_t *ticker) {
    char normalized_ticker_name[TICKER_MAX_SIZE_B];
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

    if (strlen(G_swap_ctx.received_transaction.currency_from) != normalized_ticker_len ||
        strncmp(G_swap_ctx.received_transaction.currency_from,
                normalized_ticker_name,
                normalized_ticker_len) != 0) {
        PRINTF("Error: Refund ticker '%.*s' doesn't match expected ticker '%.*s'\n",
               normalized_ticker_len,
               normalized_ticker_name,
               strlen(G_swap_ctx.received_transaction.currency_from),
               G_swap_ctx.received_transaction.currency_from);
        return false;
    }

    return true;
}

int check_refund_address(const command_t *cmd) {
    static buf_t config;
    static buf_t der;
    static buf_t address_parameters;
    static buf_t ticker;
    static buf_t application_name;

    if (parse_check_address_message(cmd, &config, &der, &address_parameters) == 0) {
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    uint8_t hash[CURVE_SIZE_BYTES];

    memset(hash, 0, sizeof(hash));

    cx_hash_sha256(config.bytes, config.size, hash, CURVE_SIZE_BYTES);

    if (cx_ecdsa_verify(&G_swap_ctx.ledger_public_key,
                        CX_LAST,
                        CX_SHA256,
                        hash,
                        CURVE_SIZE_BYTES,
                        der.bytes,
                        der.size) == 0) {
        PRINTF("Error: Fail to verify signature of coin config\n");

        return reply_error(SIGN_VERIFICATION_FAIL);
    }

    if (parse_coin_config(&config, &ticker, &application_name, &G_swap_ctx.payin_coin_config) ==
        0) {
        PRINTF("Error: Can't parse refund coin config command\n");

        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // Check that refund ticker matches the current context
    if (!check_matching_ticker(&ticker)) {
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // creating 0-terminated application name
    memset(G_swap_ctx.payin_binary_name, 0, sizeof(G_swap_ctx.payin_binary_name));
    memcpy(G_swap_ctx.payin_binary_name, PIC(application_name.bytes), application_name.size);

    if (G_swap_ctx.received_transaction
            .refund_address[sizeof(G_swap_ctx.received_transaction.refund_address) - 1] != '\0') {
        PRINTF("Address to check is not NULL terminated\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }
    // check address
    if (check_address(&G_swap_ctx.payin_coin_config,
                      &address_parameters,
                      G_swap_ctx.payin_binary_name,
                      G_swap_ctx.received_transaction.refund_address,
                      G_swap_ctx.received_transaction.refund_extra_id) != 1) {
        PRINTF("Error: Refund address validation failed\n");

        return reply_error(INVALID_ADDRESS);
    }

    if (get_printable_amount(&G_swap_ctx.payin_coin_config,
                             G_swap_ctx.payin_binary_name,
                             G_swap_ctx.received_transaction.amount_to_provider.bytes,
                             G_swap_ctx.received_transaction.amount_to_provider.size,
                             G_swap_ctx.printable_send_amount,
                             sizeof(G_swap_ctx.printable_send_amount),
                             false) < 0) {
        PRINTF("Error: Failed to get source currency printable amount\n");

        return reply_error(INTERNAL_ERROR);
    }
    PRINTF("Send amount: %s\n", G_swap_ctx.printable_send_amount);

    if (get_printable_amount(&G_swap_ctx.payin_coin_config,
                             G_swap_ctx.payin_binary_name,
                             G_swap_ctx.transaction_fee,
                             G_swap_ctx.transaction_fee_length,
                             G_swap_ctx.printable_fees_amount,
                             sizeof(G_swap_ctx.printable_fees_amount),
                             true) < 0) {
        PRINTF("Error: Failed to get source currency fees amount\n");

        return reply_error(INTERNAL_ERROR);
    }
    PRINTF("Fees: %s\n", G_swap_ctx.printable_fees_amount);

    G_swap_ctx.state = WAITING_USER_VALIDATION;
    G_swap_ctx.rate = cmd->rate;

    ui_validate_amounts();

    return 0;
}
