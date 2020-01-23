#include "check_payout_address.h"
#include "os.h"
#include "swap_errors.h"
#include "globals.h"
#include "currency_lib_calls.h"
#include "reply_error.h"
#include "parse_check_address_message.h"

int check_payout_address(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    SendFunction send) {
    unsigned char* config;
    unsigned char config_length;
    unsigned char* der;
    unsigned char der_length;
    unsigned char* address_parameters;
    unsigned char address_parameters_length;
    if (parse_check_address_message(
        input_buffer, input_buffer_length,
        &config, &config_length,
        &der, &der_length,
        &address_parameters, &address_parameters_length) == 0) {
        return reply_error(&ctx, INCORRECT_COMMAND_DATA, send);
    }
    unsigned char hash[CURVE_SIZE_BYTES];
    cx_hash_sha256(config, config_length, hash, CURVE_SIZE_BYTES);
    if (cx_ecdsa_verify(&ctx->ledger_public_key, CX_LAST, CX_SHA256, hash, CURVE_SIZE_BYTES, der, der_length) == 0) {
        PRINTF("Error: Fail to verify signature of coin config");
        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }
    // check address
    if (check_address(
        config,
        config_length,
        address_parameters,
        address_parameters_length,
        ctx->received_transaction.currency_to,
        ctx->received_transaction.payout_address,
        ctx->received_transaction.payout_extra_id) != 1) {
        PRINTF("Error: Payout address validation failed");
        return reply_error(ctx, INVALID_ADDRESS, send);
    }
    // getting printable amount
    if(get_printable_amount(
        config,
        config_length,
        ctx->received_transaction.currency_to,
        ctx->received_transaction.amount_to_wallet.bytes,
        ctx->received_transaction.amount_to_wallet.size,
        ctx->printable_get_amount,
        sizeof(ctx->printable_get_amount)) < 0) {
        PRINTF("Error: Failed to get destination currency printable amount");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }
    unsigned char output_buffer[2] = {0x90, 0x00};
    if (send(output_buffer, 2) < 0) {
        PRINTF("Error: failed to send");
        return -1;
    }
    ctx->state = TO_ADDR_CHECKED;
    return 0;
}
