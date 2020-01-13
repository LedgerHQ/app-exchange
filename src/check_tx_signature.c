#include "check_tx_signature.h"
#include "os.h"
#include "globals.h"
#include "der_serialization.h"
#include "swap_errors.h"
#include "reply_error.h"

// This function receive transaction signature 
// Input should be in the form
// 32 bytes - R part of signature
// 32 bytes - S part of signature
int check_tx_signature(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    SendFunction send) {
    if (input_buffer_length < CURVE_SIZE_BYTES * 2 + 2) {
        PRINTF("Error: Input buffer is too small");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    unsigned char der[DER_SIGNATURE_LENGTH];
    unsigned int der_length = der_serialize(
        input_buffer, CURVE_SIZE_BYTES,
        input_buffer + CURVE_SIZE_BYTES, CURVE_SIZE_BYTES,
        der, sizeof(der));
    if (der_length < 0) {
        PRINTF("Error: Can't parse signature");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    if (cx_ecdsa_verify(
        &ctx->partner.public_key,
        CX_LAST,
        CX_SHA256,
        ctx->transaction_sha256_digest,
        CURVE_SIZE_BYTES,
        der,
        der_length) == 0) {
        PRINTF("Error: Failed to verify signature of received transaction");
        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }
    unsigned char output_buffer[2] = { 0x90, 0x00 };
    if (send(output_buffer, 2) < 0) {
        PRINTF("Error: ");
        return -1;
    }
    ctx->state = SIGNATURE_CHECKED;
    return 0;
}