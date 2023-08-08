#include <os.h>
#include <cx.h>

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

#include "check_addresses_and_amounts.h"

static bool check_coin_configuration_signature(buf_t config, buf_t der) {
    uint8_t hash[CURVE_SIZE_BYTES];
    cx_hash_sha256(config.bytes, config.size, hash, CURVE_SIZE_BYTES);
    return cx_ecdsa_verify(&G_swap_ctx.ledger_public_key,
                           CX_LAST,
                           CX_SHA256,
                           hash,
                           CURVE_SIZE_BYTES,
                           der.bytes,
                           der.size);
}

static bool check_received_ticker_matches_context(buf_t ticker, const command_t *cmd) {
    char *in_currency;
    if (cmd->subcommand == SWAP || cmd->subcommand == SWAP_NG) {
        if (cmd->ins == CHECK_PAYOUT_ADDRESS) {
            in_currency = G_swap_ctx.received_transaction.currency_to;
        } else {
            in_currency = G_swap_ctx.received_transaction.currency_from;
        }
    } else if (cmd->subcommand == SELL || cmd->subcommand == SELL_NG) {
        in_currency = G_swap_ctx.sell_transaction.in_currency;
    } else {
        in_currency = G_swap_ctx.fund_transaction.in_currency;
    }
    return check_matching_ticker(ticker, in_currency);
}

static uint16_t check_relevant_address(command_e ins, buf_t sub_coin_config, buf_t address_parameters, char *appname) {
    uint8_t address_max_size;
    char *address_to_check;
    char *extra_id_to_check;

    // Depending on the current command, check either PAYOUT or REFUND
    if (ins == CHECK_PAYOUT_ADDRESS) {
        address_to_check = G_swap_ctx.received_transaction.payout_address;
        address_max_size = sizeof(G_swap_ctx.received_transaction.payout_address);
        extra_id_to_check = G_swap_ctx.received_transaction.payout_extra_id;
    } else {
        address_to_check = G_swap_ctx.received_transaction.refund_address;
        address_max_size = sizeof(G_swap_ctx.received_transaction.refund_address);
        extra_id_to_check = G_swap_ctx.received_transaction.refund_extra_id;
    }
    if (address_to_check[address_max_size - 1] != '\0') {
        PRINTF("Address to check is not NULL terminated\n");
        return INCORRECT_COMMAND_DATA;
    }

    if (check_address(&sub_coin_config,
                      &address_parameters,
                      appname,
                      address_to_check,
                      extra_id_to_check) != 1) {
        PRINTF("Error: Address validation failed\n");
        return INVALID_ADDRESS;
    }
    return 0;
}

static bool format_relevant_amount(command_e ins, buf_t sub_coin_config, char *appname) {
    pb_bytes_array_16_t *amount;
    char *dest;
    uint8_t dest_size;
    if (G_swap_ctx.subcommand == SWAP || G_swap_ctx.subcommand == SWAP_NG) {
        if (ins == CHECK_PAYOUT_ADDRESS) {
            amount = (pb_bytes_array_16_t *) &G_swap_ctx.received_transaction.amount_to_wallet;
            dest = G_swap_ctx.printable_get_amount;
            dest_size = sizeof(G_swap_ctx.printable_get_amount);
        } else {
            amount = (pb_bytes_array_16_t *) &G_swap_ctx.received_transaction.amount_to_provider;
            dest = G_swap_ctx.printable_send_amount;
            dest_size = sizeof(G_swap_ctx.printable_send_amount);
        }
    } else if (G_swap_ctx.subcommand == SELL || G_swap_ctx.subcommand == SELL_NG) {
        amount = (pb_bytes_array_16_t *) &G_swap_ctx.sell_transaction.in_amount;
        dest = G_swap_ctx.printable_send_amount;
        dest_size = sizeof(G_swap_ctx.printable_send_amount);
    } else {
        amount = (pb_bytes_array_16_t *) &G_swap_ctx.fund_transaction.in_amount;
        dest = G_swap_ctx.printable_send_amount;
        dest_size = sizeof(G_swap_ctx.printable_send_amount);
    }
    if (get_printable_amount(&sub_coin_config,
                             appname,
                             amount->bytes,
                             amount->size,
                             dest,
                             dest_size,
                             false) < 0) {
        PRINTF("Error: Failed to get printable amount\n");
        return false;
    }
    PRINTF("Formatted amount: %s\n", dest);
    return true;
}

static bool format_fees(buf_t sub_coin_config, char *appname) {
    if (get_printable_amount(&sub_coin_config,
                             appname,
                             G_swap_ctx.transaction_fee,
                             G_swap_ctx.transaction_fee_length,
                             G_swap_ctx.printable_fees_amount,
                             sizeof(G_swap_ctx.printable_fees_amount),
                             true) < 0) {
        PRINTF("Error: Failed to get printable fees amount\n");
        return false;
    }
    PRINTF("Fees: %s\n", G_swap_ctx.printable_fees_amount);
    return true;
}

static bool format_fiat_amount(void) {
    size_t len = strlen(G_swap_ctx.sell_transaction.out_currency);
    if (len + 1 >= sizeof(G_swap_ctx.printable_get_amount)) {
        return false;
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
        return false;
    }

    PRINTF("%s\n", G_swap_ctx.printable_get_amount);
    return true;
}

static void format_account_name(void) {
    strncpy(G_swap_ctx.account_name,
            G_swap_ctx.fund_transaction.account_name,
            sizeof(G_swap_ctx.account_name));
    G_swap_ctx.account_name[sizeof(G_swap_ctx.account_name) - 1] = '\x00';
}

int check_addresses_and_amounts(const command_t *cmd) {
    buf_t config;
    buf_t der;
    buf_t address_parameters;
    buf_t ticker;
    buf_t application_name;
    buf_t sub_coin_config;
    char appname[BOLOS_APPNAME_MAX_SIZE_B + 1];

    if (parse_check_address_message(cmd, &config, &der, &address_parameters) == 0) {
        PRINTF("Error: Can't parse command\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // We received the coin configuration from the CAL and it's signature. Ensure it's legitly signed by Ledger the key
    if (!check_coin_configuration_signature(config, der)) {
        PRINTF("Error: Fail to verify signature of coin config\n");
        return reply_error(SIGN_VERIFICATION_FAIL);
    }

    // Break up the configuration into its individual elements
    if (parse_coin_config(config, &ticker, &application_name, &sub_coin_config) == 0) {
        PRINTF("Error: Can't parse refund coin config command\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }
    // We can't use the pointer to the parsed application name as it is not NULL terminated
    // We have to make a local copy
    memset(appname, 0, sizeof(appname));
    memcpy(appname, application_name.bytes, application_name.size);

    // Ensure we received a coin configuration that actually serves us in the current TX context
    if (!check_received_ticker_matches_context(ticker, cmd)) {
        PRINTF("Error: received ticker doesn't match saved ticker\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // On SWAP flows we need to check refund or payout address (depending on step)
    // We received them as part of the TX but we can only check them now that we have the appname to call
    if (G_swap_ctx.subcommand == SWAP || G_swap_ctx.subcommand == SWAP_NG) {
        uint16_t ret = check_relevant_address(cmd->ins, sub_coin_config, address_parameters, appname);
        if (ret != 0) {
            return reply_error(ret);
        }
    }

    // Call the lib app to format the amount relevant to it's coin. It can be OUT going or IN coming (SWAP only)
    if (!format_relevant_amount(cmd->ins, sub_coin_config, appname)) {
        PRINTF("Error: Failed to format printable amount\n");
        return reply_error(INTERNAL_ERROR);
    }

    // Format the fees, except during CHECK_PAYOUT_ADDRESS for SWAP, (as it's done in CHECK_REFUND_ADDRESS)
    if (!((G_swap_ctx.subcommand == SWAP || G_swap_ctx.subcommand == SWAP_NG) && cmd->ins == CHECK_PAYOUT_ADDRESS)) {
        if (!format_fees(sub_coin_config, appname)) {
            PRINTF("Error: Failed to format fees amount\n");
            return reply_error(INTERNAL_ERROR);
        }
    }

    // On SELL flows we receive a FIAT amount, format it to display it on screen
    if (G_swap_ctx.subcommand == SELL || G_swap_ctx.subcommand == SELL_NG) {
        if (!format_fiat_amount()) {
            PRINTF("Error: Failed to format FIAT amount\n");
            return reply_error(INTERNAL_ERROR);
        }
    }

    // On FUND flows we display the account name that will receive the funds
    if (G_swap_ctx.subcommand == FUND || G_swap_ctx.subcommand == FUND_NG) {
        format_account_name();
    }

    // If we are in a SWAP flow at step CHECK_PAYOUT_ADDRESS, we are still waiting for CHECK_REFUND_ADDRESS
    // Otherwise we can trigger user UI validation now
    if ((G_swap_ctx.subcommand == SWAP || G_swap_ctx.subcommand == SWAP_NG) && cmd->ins == CHECK_PAYOUT_ADDRESS) {
        if (reply_success() < 0) {
            PRINTF("Error: failed to send\n");
            return -1;
        }
        G_swap_ctx.state = TO_ADDR_CHECKED;
    } else {
        // Save the paying coin appname, we'll need it to start the app during START_SIGNING step
        memcpy(G_swap_ctx.payin_binary_name, appname, sizeof(appname));

        // Save the paying sub coin configuration as the lib app will need it to sign
        G_swap_ctx.paying_sub_coin_config_size = sub_coin_config.size;
        memset(G_swap_ctx.paying_sub_coin_config, 0, sizeof(G_swap_ctx.paying_sub_coin_config));
        memcpy(G_swap_ctx.paying_sub_coin_config, sub_coin_config.bytes, sub_coin_config.size);

        G_swap_ctx.state = WAITING_USER_VALIDATION;
        G_swap_ctx.rate = cmd->rate;

        ui_validate_amounts();
    }

    return 0;
}
