#include <os.h>
#include <cx.h>

#include "check_payout_address.h"
#include "swap_errors.h"
#include "globals.h"
#include "currency_lib_calls.h"
#include "io.h"
#include "parse_check_address_message.h"
#include "parse_coin_config.h"
#include "printable_amount.h"
#include "menu.h"

int check_payout_address(const command_t *cmd) {
    static buf_t config;
    static buf_t der;
    static buf_t address_parameters;
    static buf_t ticker;
    static buf_t application_name;

    if (parse_check_address_message(cmd, &config, &der, &address_parameters) == 0) {
        PRINTF("Error: Can't parse CHECK_PAYOUT_ADDRESS command\n");

        return reply_error(INCORRECT_COMMAND_DATA);
    }

    PRINTF("CHECK_PAYOUT_ADDRESS parsed OK\n");

    uint8_t hash[CURVE_SIZE_BYTES];

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

    if (parse_coin_config(&config, &ticker, &application_name, &config) == 0) {
        PRINTF("Error: Can't parse payout coin config command\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // Check that given ticker match current context
    if (strlen(G_swap_ctx.received_transaction.currency_to) != ticker.size ||
        strncmp(G_swap_ctx.received_transaction.currency_to,
                (const char *) ticker.bytes,
                ticker.size) != 0) {
        PRINTF("Error: Payout ticker doesn't match configuration ticker\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    PRINTF("Coin config parsed OK\n");

    // creating 0-terminated application name
    memset(G_swap_ctx.payin_binary_name, 0, sizeof(G_swap_ctx.payin_binary_name));
    memcpy(G_swap_ctx.payin_binary_name, application_name.bytes, application_name.size);

    PRINTF("PATH inside the SWAP = %.*H\n", address_parameters.size, address_parameters.bytes);

    if (G_swap_ctx.received_transaction
            .payout_address[sizeof(G_swap_ctx.received_transaction.payout_address) - 1] != '\0') {
        PRINTF("Address to check is not NULL terminated\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // check address
    if (check_address(&config,
                      &address_parameters,
                      G_swap_ctx.payin_binary_name,
                      G_swap_ctx.received_transaction.payout_address,
                      G_swap_ctx.received_transaction.payout_extra_id) != 1) {
        PRINTF("Error: Payout address validation failed\n");
        return reply_error(INVALID_ADDRESS);
    }

    PRINTF("Payout address is OK\n");

    // getting printable amount
    if (get_printable_amount(&config,
                             G_swap_ctx.payin_binary_name,
                             (uint8_t *) G_swap_ctx.received_transaction.amount_to_wallet.bytes,
                             G_swap_ctx.received_transaction.amount_to_wallet.size,
                             G_swap_ctx.printable_get_amount,
                             sizeof(G_swap_ctx.printable_get_amount),
                             false) < 0) {
        PRINTF("Error: Failed to get destination currency printable amount\n");
        return reply_error(INTERNAL_ERROR);
    }

    PRINTF("Amount = %s\n", G_swap_ctx.printable_get_amount);

    if (reply_success() < 0) {
        PRINTF("Error: failed to send\n");
        return -1;
    }

    G_swap_ctx.state = TO_ADDR_CHECKED;

    return 0;
}
