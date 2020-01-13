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
    if (input_buffer_length < 72) {
        PRINTF("Error: Input buffer is too small to contain correct CHECK_REFUND_ADDRESS message");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    // parse message
    ctx->payin_coin_config_length = input_buffer[0];
    if (input_buffer_length < 2 + DER_SIGNATURE_LENGTH + ctx->payin_coin_config_length) {
        PRINTF("Error: Input buffer is too small to contain correct CHECK_REFUND_ADDRESS message");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    unsigned char hash[CURVE_SIZE_BYTES];
    os_memcpy(ctx->payin_coin_config, input_buffer + 1, ctx->payin_coin_config_length);
    cx_hash_sha256(ctx->payin_coin_config, ctx->payin_coin_config_length, hash, CURVE_SIZE_BYTES);
    if (cx_ecdsa_verify(&ctx->ledger_public_key, CX_LAST, CX_SHA256, hash, CURVE_SIZE_BYTES, input_buffer + 1 + ctx->payin_coin_config_length, DER_SIGNATURE_LENGTH) == 0) {
        PRINTF("Error: Fail to verify signature of coin config");
        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }
    // check address
    if (check_address(
        ctx->payin_coin_config,
        ctx->payin_coin_config_length,
        input_buffer + 1 + ctx->payin_coin_config_length + DER_SIGNATURE_LENGTH + 1,
        input_buffer[1 + ctx->payin_coin_config_length + DER_SIGNATURE_LENGTH],
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