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
    return cx_ecdsa_verify_no_throw(&G_swap_ctx.ledger_public_key,
                                    hash,
                                    CURVE_SIZE_BYTES,
                                    der.bytes,
                                    der.size);
}

static bool check_received_ticker_matches_context(buf_t ticker, const command_t *cmd) {
    char *in_currency;
    if (cmd->subcommand == SWAP || cmd->subcommand == SWAP_NG) {
        if (cmd->ins == CHECK_PAYOUT_ADDRESS) {
            in_currency = G_swap_ctx.swap_transaction.currency_to;
        } else {
            in_currency = G_swap_ctx.swap_transaction.currency_from;
        }
    } else if (cmd->subcommand == SELL || cmd->subcommand == SELL_NG) {
        in_currency = G_swap_ctx.sell_transaction.in_currency;
    } else {
        in_currency = G_swap_ctx.fund_transaction.in_currency;
    }
    return check_matching_ticker(ticker, in_currency);
}

static uint16_t check_payout_or_refund_address(command_e ins,
                                               buf_t sub_coin_config,
                                               buf_t address_parameters,
                                               char *appname) {
    uint8_t address_max_size;
    char *address_to_check;
    char *extra_id_to_check;

    // Depending on the current command, check either PAYOUT or REFUND
    if (ins == CHECK_PAYOUT_ADDRESS) {
        address_to_check = G_swap_ctx.swap_transaction.payout_address;
        address_max_size = sizeof(G_swap_ctx.swap_transaction.payout_address);
        extra_id_to_check = G_swap_ctx.swap_transaction.payout_extra_id;
    } else {
        address_to_check = G_swap_ctx.swap_transaction.refund_address;
        address_max_size = sizeof(G_swap_ctx.swap_transaction.refund_address);
        extra_id_to_check = G_swap_ctx.swap_transaction.refund_extra_id;
    }
    if (address_to_check[address_max_size - 1] != '\0') {
        PRINTF("Address to check is not NULL terminated\n");
        return INCORRECT_COMMAND_DATA;
    }

    uint16_t err = check_address(&sub_coin_config,
                                 &address_parameters,
                                 appname,
                                 address_to_check,
                                 extra_id_to_check);
    if (err != 0) {
        PRINTF("Error: check_address failed\n");
        return err;
    }
    return 0;
}

static uint16_t format_relevant_amount(command_e ins, buf_t sub_coin_config, char *appname) {
    pb_bytes_array_16_t *amount;
    char *dest;
    uint8_t dest_size;
    if (G_swap_ctx.subcommand == SWAP || G_swap_ctx.subcommand == SWAP_NG) {
        if (ins == CHECK_PAYOUT_ADDRESS) {
            amount = (pb_bytes_array_16_t *) &G_swap_ctx.swap_transaction.amount_to_wallet;
            dest = G_swap_ctx.printable_get_amount;
            dest_size = sizeof(G_swap_ctx.printable_get_amount);
        } else {
            amount = (pb_bytes_array_16_t *) &G_swap_ctx.swap_transaction.amount_to_provider;
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

    uint16_t err = get_printable_amount(&sub_coin_config,
                                        appname,
                                        amount->bytes,
                                        amount->size,
                                        dest,
                                        dest_size,
                                        false);
    if (err != 0) {
        PRINTF("Error: Failed to get printable amount\n");
        return err;
    }
    PRINTF("Formatted amount: %s\n", dest);
    return 0;
}

static uint16_t format_fees(buf_t sub_coin_config, char *appname) {
    uint16_t err = get_printable_amount(&sub_coin_config,
                                        appname,
                                        G_swap_ctx.transaction_fee,
                                        G_swap_ctx.transaction_fee_length,
                                        G_swap_ctx.printable_fees_amount,
                                        sizeof(G_swap_ctx.printable_fees_amount),
                                        true);
    if (err != 0) {
        PRINTF("Error: Failed to get printable fees amount\n");
        return err;
    }
    PRINTF("Fees: %s\n", G_swap_ctx.printable_fees_amount);
    return 0;
}

static bool format_fiat_amount(void) {
    size_t len = strlen(G_swap_ctx.sell_transaction.out_currency);
    if (len + 1 >= sizeof(G_swap_ctx.printable_get_amount)) {
        return false;
    }

    strlcpy(G_swap_ctx.printable_get_amount,
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
    strlcpy(G_swap_ctx.account_name,
            G_swap_ctx.fund_transaction.account_name,
            sizeof(G_swap_ctx.account_name));
    G_swap_ctx.account_name[sizeof(G_swap_ctx.account_name) - 1] = '\x00';
}

// Three possibilities in this function:
// - we are in CHECK_ASSET_IN (FUND or SELL flows)
//     - we will ask the FROM app to format the FROM amount and the fees
//     - we will format the FIAT amount TO (SELL flow)
//     - we will format the UI account field (FUND flow)
// - we are in CHECK_PAYOUT_ADDRESS (SWAP flow)
//     - we will ask the TO app to format the TO amount
//     - we will ask the TO app to check the payout address
// - we are in CHECK_REFUND_ADDRESS (SWAP flow)
//     - we will ask the FROM app to format the FROM amount and the fees
//     - we will ask the FROM app to check the refund address
int check_addresses_and_amounts(const command_t *cmd) {
    buf_t config;
    buf_t der;
    buf_t address_parameters;
    buf_t ticker;
    buf_t parsed_application_name;
    buf_t sub_coin_config;
    char application_name[BOLOS_APPNAME_MAX_SIZE_B + 1];
    uint16_t err;

    if (parse_check_address_message(cmd, &config, &der, &address_parameters) == 0) {
        PRINTF("Error: Can't parse command\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // We received the coin configuration from the CAL and its signature. Check the signature
    if (!check_coin_configuration_signature(config, der)) {
        PRINTF("Error: Fail to verify signature of coin config\n");
        return reply_error(SIGN_VERIFICATION_FAIL);
    }

    // Break up the configuration into its individual elements
    if (!parse_coin_config(config, &ticker, &parsed_application_name, &sub_coin_config)) {
        PRINTF("Error: Can't parse coin config command\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // We can't use the pointer to the parsed application name as it is not NULL terminated
    // We have to make a local copy
    memset(application_name, 0, sizeof(application_name));
    memcpy(application_name, parsed_application_name.bytes, parsed_application_name.size);

    // Ensure we received a coin configuration that actually serves us in the current TX context
    if (!check_received_ticker_matches_context(ticker, cmd)) {
        PRINTF("Error: received ticker doesn't match saved ticker\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // On SWAP flows we need to check refund or payout address (depending on step)
    // We received them as part of the TX but we couldn't check then as we did not have the
    // application_name yet
    if (G_swap_ctx.subcommand == SWAP || G_swap_ctx.subcommand == SWAP_NG) {
        uint16_t ret = check_payout_or_refund_address(cmd->ins,
                                                      sub_coin_config,
                                                      address_parameters,
                                                      application_name);
        if (ret != 0) {
            return reply_error(ret);
        }
    }

    // Call the lib app to format the amount according to its coin.
    // It can be the OUT going amount or IN coming amount for SWAP
    err = format_relevant_amount(cmd->ins, sub_coin_config, application_name);
    if (err != 0) {
        PRINTF("Error: Failed to format printable amount\n");
        return reply_error(err);
    }

    // Format the fees, except during CHECK_PAYOUT_ADDRESS for SWAP, (it's done in
    // CHECK_REFUND_ADDRESS as the fees are in the OUT going currency)
    if (!((G_swap_ctx.subcommand == SWAP || G_swap_ctx.subcommand == SWAP_NG) &&
          cmd->ins == CHECK_PAYOUT_ADDRESS)) {
        err = format_fees(sub_coin_config, application_name);
        if (err != 0) {
            PRINTF("Error: Failed to format fees amount\n");
            return reply_error(err);
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

    // If we are in a SWAP flow at step CHECK_PAYOUT_ADDRESS, we are still waiting for
    // CHECK_REFUND_ADDRESS
    // Otherwise we can trigger the UI to get user validation now
    if ((G_swap_ctx.subcommand == SWAP || G_swap_ctx.subcommand == SWAP_NG) &&
        cmd->ins == CHECK_PAYOUT_ADDRESS) {
        if (reply_success() < 0) {
            PRINTF("Error: failed to send\n");
            return -1;
        }
        G_swap_ctx.state = TO_ADDR_CHECKED;
    } else {
        // Save the paying coin application_name, we'll need it to start the app during
        // START_SIGNING step
        memcpy(G_swap_ctx.payin_binary_name, application_name, sizeof(application_name));

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
