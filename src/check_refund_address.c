#include "check_refund_address.h"
#include "os.h"
#include "currency_lib_calls.h"
#include "globals.h"
#include "swap_errors.h"
#include "reply_error.h"
#include "parse_check_address_message.h"
#include "menu.h"
#include "parse_coin_config.h"

swap_app_context_t *application_context;
SendFunction send_function;

void on_accept() {
    // user accepted
    unsigned char output_buffer[2] = {0x90, 0x00};
    if (send_function(output_buffer, 2) < 0) {
        PRINTF("Error: Failed to send\n");
        return;
    }
    application_context->state = WAITING_SIGNING;
}

void on_reject() {
    PRINTF("User refused transaction\n");
    reply_error(application_context, USER_REFUSED, send_function);
}

int check_refund_address(subcommand_e subcommand,                                        //
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
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    static unsigned char hash[CURVE_SIZE_BYTES];
    memset(hash, 0, sizeof(hash));
    cx_hash_sha256(config, config_length, hash, CURVE_SIZE_BYTES);
    if (cx_ecdsa_verify(&ctx->ledger_public_key, CX_LAST, CX_SHA256, hash, CURVE_SIZE_BYTES, der,
                        der_length) == 0) {
        PRINTF("Error: Fail to verify signature of coin config");
        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }
    if (parse_coin_config(config, config_length,                        //
                          &ticker, &ticker_length,                      //
                          &application_name, &application_name_length,  //
                          &ctx->payin_coin_config,                      //
                          (unsigned char *) &ctx->payin_coin_config_length) == 0) {
        PRINTF("Error: Can't parse refund coin config command\n");
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
    if (strlen(ctx->received_transaction.currency_from) != ticker_length ||
        strncmp(ctx->received_transaction.currency_from,  //
                (const char *) ticker,                    //
                ticker_length) != 0) {
        PRINTF("Error: Refund ticker doesn't match configuration ticker\n");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    // creating 0-terminated application name
    os_memset(ctx->payin_binary_name, 0, sizeof(ctx->payin_binary_name));
    os_memcpy(ctx->payin_binary_name, application_name, application_name_length);
    // check address
    if (check_address(ctx->payin_coin_config, ctx->payin_coin_config_length,  //
                      address_parameters, address_parameters_length,          //
                      ctx->payin_binary_name,                                 //
                      ctx->received_transaction.refund_address,               //
                      ctx->received_transaction.refund_extra_id) != 1) {
        PRINTF("Error: Refund address validation failed");
        return reply_error(ctx, INVALID_ADDRESS, send);
    }
    static char printable_send_amount[30];
    memset(printable_send_amount, 0, sizeof(printable_send_amount));
    if (get_printable_amount(ctx->payin_coin_config, ctx->payin_coin_config_length,  //
                             ctx->payin_binary_name,                                 //
                             ctx->received_transaction.amount_to_provider.bytes,     //
                             ctx->received_transaction.amount_to_provider.size,      //
                             printable_send_amount, sizeof(printable_send_amount),   //
                             false) < 0) {
        PRINTF("Error: Failed to get source currency printable amount");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }
    static char printable_fees_amount[30];
    memset(printable_fees_amount, 0, sizeof(printable_fees_amount));
    if (get_printable_amount(ctx->payin_coin_config, ctx->payin_coin_config_length,  //
                             ctx->payin_binary_name,                                 //
                             ctx->transaction_fee, ctx->transaction_fee_length,      //
                             printable_fees_amount, sizeof(printable_fees_amount),   //
                             true) < 0) {
        PRINTF("Error: Failed to get source currency fees amount");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }

    ctx->state = WAITING_USER_VALIDATION;
    application_context = ctx;
    send_function = send;
    ui_validate_amounts(printable_send_amount, ctx->printable_get_amount, printable_fees_amount,
                        on_accept, on_reject);
    return 0;
}