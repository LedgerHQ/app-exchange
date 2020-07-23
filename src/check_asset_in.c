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

int check_asset_in(subcommand_e subcommand,                                        //
                   swap_app_context_t *ctx,                                        //
                   unsigned char *input_buffer, unsigned int input_buffer_length,  //
                   SendFunction send) {
    static unsigned char *config;
    static unsigned char config_length;
    static unsigned char *der;
    static unsigned char der_length;
    static unsigned char *address_parameters;
    static unsigned char address_parameters_length;
    static unsigned char *ticker;
    static unsigned char ticker_length;
    static unsigned char *application_name;
    static unsigned char application_name_length;

    if (parse_check_address_message(input_buffer, input_buffer_length,  //
                                    &config, &config_length,            //
                                    &der, &der_length,                  //
                                    &address_parameters, &address_parameters_length) == 0) {
        PRINTF("Error: Can't parse CHECK_ASSET_IN command\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    static unsigned char hash[CURVE_SIZE_BYTES];

    cx_hash_sha256(config, config_length, hash, CURVE_SIZE_BYTES);

    if (cx_ecdsa_verify(&ctx->ledger_public_key, CX_LAST, CX_SHA256, hash, CURVE_SIZE_BYTES, der,
                        der_length) == 0) {
        PRINTF("Error: Fail to verify signature of coin config\n");

        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }

    if (parse_coin_config(config, config_length,                        //
                          &ticker, &ticker_length,                      //
                          &application_name, &application_name_length,  //
                          &config, &config_length) == 0) {
        PRINTF("Error: Can't parse payout coin config command\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    if (ticker_length < 2 || ticker_length > 9) {
        PRINTF("Error: Ticker length should be in [3, 9]\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    if (application_name_length < 3 || application_name_length > 15) {
        PRINTF("Error: Application name should be in [3, 15]\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    // Check that given ticker match current context
    if (strlen(ctx->sell_transaction.in_currency) != ticker_length ||
        strncmp(ctx->sell_transaction.in_currency, (const char *) ticker, ticker_length) != 0) {
        PRINTF("Error: Payout ticker doesn't match configuration ticker\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    PRINTF("Coin config parsed OK\n");

    // creating 0-terminated application name
    os_memset(ctx->payin_binary_name, 0, sizeof(ctx->payin_binary_name));
    os_memcpy(ctx->payin_binary_name, application_name, application_name_length);

    PRINTF("PATH inside the SWAP = %.*H\n", address_parameters_length, address_parameters);

    static char in_printable_amount[30];

    // getting printable amount
    if (get_printable_amount(config, config_length,                             //
                             ctx->payin_binary_name,                            //
                             ctx->sell_transaction.in_amount.bytes,             //
                             ctx->sell_transaction.in_amount.size,              //
                             in_printable_amount, sizeof(in_printable_amount),  //
                             false) < 0) {
        PRINTF("Error: Failed to get destination currency printable amount\n");

        return reply_error(ctx, INTERNAL_ERROR, send);
    }

    PRINTF("Amount = %s\n", in_printable_amount);

    static char printable_fees_amount[30];
    os_memset(printable_fees_amount, 0, sizeof(printable_fees_amount));

    if (get_printable_amount(ctx->payin_coin_config, ctx->payin_coin_config_length,  //
                             ctx->payin_binary_name,                                 //
                             ctx->transaction_fee, ctx->transaction_fee_length,      //
                             printable_fees_amount, sizeof(printable_fees_amount),   //
                             true) < 0) {
        PRINTF("Error: Failed to get source currency fees amount");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }

    ctx->state = WAITING_USER_VALIDATION;

    strcpy(ctx->printable_get_amount, ctx->sell_transaction.out_currency);
    strncat(ctx->printable_get_amount, " ", 1);

    if (get_fiat_printable_amount(
            ctx->sell_transaction.out_amount.coefficient.bytes,                                 //
            ctx->sell_transaction.out_amount.coefficient.size,                                  //
            ctx->sell_transaction.out_amount.exponent,                                          //
            ctx->printable_get_amount + strlen(ctx->sell_transaction.out_currency) + 1,         //
            sizeof(ctx->printable_get_amount) - strlen(ctx->sell_transaction.out_currency) + 1  //
            ) < 0) {
        PRINTF("Error: Failed to get source currency printable amount\n");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }

    PRINTF("%s\n", ctx->printable_get_amount);

    ui_validate_amounts(subcommand,             //
                        ctx,                    //
                        in_printable_amount,    //
                        printable_fees_amount,  //
                        send);

    unsigned char output_buffer[2] = {0x90, 0x00};

    if (send(output_buffer, 2) < 0) {
        PRINTF("Error: failed to send\n");

        return -1;
    }

    return 0;
}
