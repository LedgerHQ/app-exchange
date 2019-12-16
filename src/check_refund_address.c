#include "check_refund_address.h"
#include "os.h"
#include "globals.h"
#include "check_address.h"
#include "user_validate_amounts.h"
#include "errors.h"

int check_refund_address(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    unsigned char* output_buffer, int output_buffer_length) {
    if (input_buffer_length < 72) {
        PRINTF("Error: Input buffer is too small to contain correct CHECK_REFUND_ADDRESS message");
        THROW(INCORRECT_COMMAND_DATA);
    }
    // parse message
    unsigned char config_length = input_buffer[0];
    if (input_buffer_length < 2 + DER_SIGNATURE_LENGTH + config_length) {
        PRINTF("Error: Input buffer is too small to contain correct CHECK_REFUND_ADDRESS message");
        THROW(INCORRECT_COMMAND_DATA);
    }
    unsigned char hash[CURVE_SIZE_BYTES];
    cx_hash_sha256(input_buffer + 1, config_length, hash, CURVE_SIZE_BYTES);
    if (cx_ecdsa_verify(&ctx->ledger_public_key, CX_LAST, CX_SHA256, hash, CURVE_SIZE_BYTES, input_buffer + 1 + config_length, DER_SIGNATURE_LENGTH) == 0) {
        PRINTF("Error: Fail to verify signature of coin config");
        THROW(SIGN_VERIFICATION_FAIL);
    }
    // check address
    if (!check_address(
        input_buffer + 1,
        config_length,
        input_buffer + 1 + config_length + DER_SIGNATURE_LENGTH + 1,
        input_buffer[1 + config_length + DER_SIGNATURE_LENGTH],
        ctx->received_transaction.currency_from,
        sizeof(ctx->received_transaction.currency_from),
        ctx->received_transaction.refund_address,
        sizeof(ctx->received_transaction.refund_address),
        ctx->received_transaction.refund_extra_id,
        sizeof(ctx->received_transaction.refund_extra_id))) {
        PRINTF("Error: Refund address validation failed");
        THROW(INVALID_ADDRESS);
    }
    if (!user_validate_amounts(
        ctx->received_transaction.currency_from,
        sizeof(ctx->received_transaction.currency_from),
        ctx->received_transaction.currency_to,
        sizeof(ctx->received_transaction.currency_to),
        ctx->received_transaction.amount_to_provider.bytes,
        ctx->received_transaction.amount_to_provider.size,
        ctx->received_transaction.amount_to_wallet.bytes,
        ctx->received_transaction.amount_to_wallet.size,
        ctx->partner.name,
        ctx->partner.name_length)) {
        PRINTF("Error: User refused to accept transaction");
        THROW(USER_REFUSED);
    }
}