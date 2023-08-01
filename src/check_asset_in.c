#include <os.h>
#include <cx.h>

#include "check_asset_in.h"
#include "swap_errors.h"
#include "globals.h"
#include "currency_lib_calls.h"
#include "io.h"
#include "parse_check_address_message.h"
#include "parse_coin_config.h"
#include "printable_amount.h"
#include "validate_transaction.h"
#include "menu.h"
#include "pb_structs.h"
#include "ticker_normalization.h"

int check_asset_in(const command_t *cmd) {
    static buf_t config;
    static buf_t der;
    static buf_t address_parameters;
    static buf_t ticker;
    static buf_t application_name;

    if (parse_check_address_message(cmd, &config, &der, &address_parameters) == 0) {
        PRINTF("Error: Can't parse CHECK_ASSET_IN command\n");

        return reply_error(INCORRECT_COMMAND_DATA);
    }

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

    if (parse_coin_config(&config, &ticker, &application_name, &G_swap_ctx.payin_coin_config) ==
        0) {
        PRINTF("Error: Can't parse CRYPTO coin config command\n");

        return reply_error(INCORRECT_COMMAND_DATA);
    }

    PRINTF("G_swap_ctx.subcommand = %d\n", G_swap_ctx.subcommand);
    if (G_swap_ctx.subcommand == SELL || G_swap_ctx.subcommand == SELL_NG) {
        // Check that ticker matches the current context
        if (!check_matching_ticker(&ticker, G_swap_ctx.sell_transaction.in_currency)) {
            PRINTF("G_swap_ctx.sell_transaction.in_currency = %s\n", G_swap_ctx.sell_transaction.in_currency);
            PRINTF("Error: ticker doesn't match configuration ticker\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }
    } else {
        // Check that ticker matches the current context
        if (!check_matching_ticker(&ticker, G_swap_ctx.fund_transaction.in_currency)) {
            PRINTF("Error: ticker doesn't match configuration ticker\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }
    }

    PRINTF("Coin configuration parsed: OK\n");

    // creating 0-terminated application name
    memset(G_swap_ctx.payin_binary_name, 0, sizeof(G_swap_ctx.payin_binary_name));
    memcpy(G_swap_ctx.payin_binary_name, PIC(application_name.bytes), application_name.size);

    PRINTF("PATH inside the SWAP = %.*H\n", address_parameters.size, address_parameters.bytes);

    pb_bytes_array_16_t *in_amount;
    if (G_swap_ctx.subcommand == SELL || G_swap_ctx.subcommand == SELL_NG) {
        in_amount = (pb_bytes_array_16_t *) &G_swap_ctx.sell_transaction.in_amount;
    } else {
        in_amount = (pb_bytes_array_16_t *) &G_swap_ctx.fund_transaction.in_amount;
    }

    // getting printable amount
    if (get_printable_amount(&G_swap_ctx.payin_coin_config,
                             G_swap_ctx.payin_binary_name,
                             (uint8_t *) in_amount->bytes,
                             in_amount->size,
                             G_swap_ctx.printable_send_amount,
                             sizeof(G_swap_ctx.printable_send_amount),
                             false) < 0) {
        PRINTF("Error: Failed to get CRYPTO currency printable amount\n");

        return reply_error(INTERNAL_ERROR);
    }

    PRINTF("Amount = %s\n", G_swap_ctx.printable_send_amount);

    if (get_printable_amount(&G_swap_ctx.payin_coin_config,
                             G_swap_ctx.payin_binary_name,
                             (uint8_t *) G_swap_ctx.transaction_fee,
                             G_swap_ctx.transaction_fee_length,
                             G_swap_ctx.printable_fees_amount,
                             sizeof(G_swap_ctx.printable_fees_amount),
                             true) < 0) {
        PRINTF("Error: Failed to get CRYPTO currency fees amount");
        return reply_error(INTERNAL_ERROR);
    }

    if (G_swap_ctx.subcommand == SELL || G_swap_ctx.subcommand == SELL_NG) {
        size_t len = strlen(G_swap_ctx.sell_transaction.out_currency);
        if (len + 1 >= sizeof(G_swap_ctx.printable_get_amount)) {
            return reply_error(INTERNAL_ERROR);
        }

        strncpy(G_swap_ctx.printable_get_amount,
                G_swap_ctx.sell_transaction.out_currency,
                sizeof(G_swap_ctx.printable_get_amount));
        G_swap_ctx.printable_get_amount[len] = ' ';
        G_swap_ctx.printable_get_amount[len + 1] = '\x00';

        if (get_fiat_printable_amount(G_swap_ctx.sell_transaction.out_amount.coefficient.bytes,
                                      G_swap_ctx.sell_transaction.out_amount.coefficient.size,
                                      G_swap_ctx.sell_transaction.out_amount.exponent,
                                      G_swap_ctx.printable_get_amount + len + 1,
                                      sizeof(G_swap_ctx.printable_get_amount) - (len + 1)) < 0) {
            PRINTF("Error: Failed to get source currency printable amount\n");
            return reply_error(INTERNAL_ERROR);
        }

        PRINTF("%s\n", G_swap_ctx.printable_get_amount);
    } else {
        // Prepare message for account funding
        strncpy(G_swap_ctx.printable_get_amount,
                G_swap_ctx.fund_transaction.account_name,
                sizeof(G_swap_ctx.printable_get_amount));
        G_swap_ctx.printable_get_amount[sizeof(G_swap_ctx.printable_get_amount) - 1] = '\x00';
    }

    G_swap_ctx.state = WAITING_USER_VALIDATION;
    G_swap_ctx.rate = cmd->rate;

    ui_validate_amounts();

    return 0;
}
