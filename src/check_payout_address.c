#include "check_payout_address.h"
#include "os.h"
#include "swap_errors.h"
#include "globals.h"
#include "currency_lib_calls.h"
#include "reply_error.h"
#include "parse_check_address_message.h"
#include "parse_coin_config.h"

int check_payout_address(subcommand_e subcommand,                                        //
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
        PRINTF("Error: Can't parse CHECK_PAYOUT_ADDRESS command\n");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    PRINTF("CHECK_PAYOUT_ADDRESS parsed OK\n");
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
    if (strlen(ctx->received_transaction.currency_to) != ticker_length ||
        strncmp(ctx->received_transaction.currency_to, (const char *) ticker, ticker_length) != 0) {
        PRINTF("Error: Payout ticker doesn't match configuration ticker\n");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    PRINTF("Coin config parsed OK\n");
    // creating 0-terminated application name
    static char app_name[16];
    os_memcpy(app_name, application_name, application_name_length);
    app_name[application_name_length] = 0;
    PRINTF("PATH inside the SWAP = %.*H\n", address_parameters_length, address_parameters);
    // check address
    if (check_address(config, config_length,                          //
                      address_parameters, address_parameters_length,  //
                      app_name,                                       //
                      ctx->received_transaction.payout_address,       //
                      ctx->received_transaction.payout_extra_id) != 1) {
        PRINTF("Error: Payout address validation failed\n");
        return reply_error(ctx, INVALID_ADDRESS, send);
    }
    PRINTF("Payout address is OK\n");
    // getting printable amount
    if (get_printable_amount(config, config_length,                                         //
                             app_name,                                                      //
                             ctx->received_transaction.amount_to_wallet.bytes,              //
                             ctx->received_transaction.amount_to_wallet.size,               //
                             ctx->printable_get_amount, sizeof(ctx->printable_get_amount),  //
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
