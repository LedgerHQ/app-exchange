#include "check_payout_address.h"
#include "os.h"
#include "swap_errors.h"
#include "globals.h"
#include "currency_lib_calls.h"
#include "reply_error.h"

// 1 byte length X of "to" currency configuration 
// X bytes "to" currency configuration
// 70 bytes DER serialized signature
// 1 byte length Y of address paramaters (path, version etc.)
// Y bytes of address parameters
int check_payout_address(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    SendFunction send) {
    if (input_buffer_length < 72) {
        PRINTF("Error: Input buffer is too small to contain correct CHECK_PAYOUT_ADDRESS message");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    // parse message
    unsigned char config_length = input_buffer[0];
    if (input_buffer_length < 2 + DER_SIGNATURE_LENGTH + config_length) {
        PRINTF("Error: Input buffer is too small to contain correct CHECK_PAYOUT_ADDRESS message");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    unsigned char hash[CURVE_SIZE_BYTES];
    cx_hash_sha256(input_buffer + 1, config_length, hash, CURVE_SIZE_BYTES);
    if (cx_ecdsa_verify(&ctx->ledger_public_key, CX_LAST, CX_SHA256, hash, CURVE_SIZE_BYTES, input_buffer + 1 + config_length, DER_SIGNATURE_LENGTH) == 0) {
        PRINTF("Error: Fail to verify signature of coin config");
        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }
    // check address
    if (check_address(
        input_buffer + 1,
        config_length,
        input_buffer + 1 + config_length + DER_SIGNATURE_LENGTH + 1,
        input_buffer[1 + config_length + DER_SIGNATURE_LENGTH],
        ctx->received_transaction.currency_to,
        ctx->received_transaction.payout_address,
        ctx->received_transaction.payout_extra_id) != 1) {
        PRINTF("Error: Payout address validation failed");
        return reply_error(ctx, INVALID_ADDRESS, send);
    }
    PRINTF("Payout address validated");
    // getting printable amount
    if(get_printable_amount(
        input_buffer + 1,
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
