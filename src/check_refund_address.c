#include "check_refund_address.h"
#include "os.h"
#include "globals.h"
#include "currency_lib_calls.h"
#include "currency_application_map.h"
#include "user_validate_amounts.h"
#include "swap_errors.h"
#include "reply_error.h"

int check_refund_address(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    SendFunction send) {
    unsigned char* config;
    unsigned char* der;
    unsigned char der_length;
    unsigned char* address_parameters;
    unsigned char address_parameters_length;
    if (parse_check_address_message(
        input_buffer, input_buffer_length,
        &config, &ctx->payin_coin_config_length,
        &der, &der_length,
        &address_parameters, &address_parameters_length) == 0) {
        return reply_error(&ctx, INCORRECT_COMMAND_DATA, send);
    }
    // copy payin configuration, we will need it later
    if (ctx->payin_coin_config_length > sizeof(ctx->payin_coin_config)) {
        PRINTF("Error: Currency config is too big");
        return reply_error(&ctx, INCORRECT_COMMAND_DATA, send);
    }
    os_memcpy(ctx->payin_coin_config, config, ctx->payin_coin_config_length);
    unsigned char hash[CURVE_SIZE_BYTES];
    cx_hash_sha256(ctx->payin_coin_config, ctx->payin_coin_config_length, hash, CURVE_SIZE_BYTES);
    if (cx_ecdsa_verify(&ctx->ledger_public_key, CX_LAST, CX_SHA256, hash, CURVE_SIZE_BYTES, der, der_length) == 0) {
        PRINTF("Error: Fail to verify signature of coin config");
        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }
    // check address
    if (check_address(
        ctx->payin_coin_config,
        ctx->payin_coin_config_length,
        address_parameters,
        address_parameters_length,
        ctx->received_transaction.currency_from,
        ctx->received_transaction.refund_address,
        ctx->received_transaction.refund_extra_id) < 0) {
        PRINTF("Error: Refund address validation failed");
        return reply_error(ctx, INVALID_ADDRESS, send);
    }
    char printable_send_amount[30] = {0};
    if (get_printable_amount(
        ctx->payin_coin_config,
        ctx->payin_coin_config_length,
        ctx->received_transaction.currency_from,
        ctx->received_transaction.amount_to_provider.bytes,
        ctx->received_transaction.amount_to_provider.size,
        printable_send_amount,
        sizeof(printable_send_amount)) < 0) {
        PRINTF("Error: Failed to get source currency printable amount");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }
    return user_validate_amounts(printable_send_amount, ctx->printable_get_amount, ctx->partner.name, ctx, send);
}