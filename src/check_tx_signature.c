#include "check_tx_signature.h"
#include "os.h"
#include "globals.h"
#include "der_serialization.h"
#include "errors.h"

// This function receive transaction signature 
// Input should be in the form
// 32 bytes - R part of signature
// 32 bytes - S part of signature
int check_tx_signature(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    unsigned char* output_buffer, int output_buffer_length) {
    
    if (input_buffer_length < CURVE_SIZE_BYTES * 2 + 2) {
        PRINTF("Error: Input buffer is too small");
        THROW(INCORRECT_COMMAND_DATA);
    }
    unsigned char der[DER_SIGNATURE_LENGTH];
    unsigned int der_length = der_serialize(
        input_buffer, CURVE_SIZE_BYTES,
        input_buffer + CURVE_SIZE_BYTES, CURVE_SIZE_BYTES,
        der, sizeof(der));
    if (cx_ecdsa_verify(
        &ctx->partner.public_key,
        CX_LAST,
        CX_SHA256,
        ctx->transaction_sha256_digest,
        CURVE_SIZE_BYTES,
        der,
        der_length) == 0) {
        PRINTF("Error: Failed to verify signature of received transaction");
        THROW(SIGN_VERIFICATION_FAIL);
    }
    if (output_buffer_length < 2) {
        PRINTF("Error: Output buffer is too small");
        THROW(OUTPUT_BUFFER_IS_TOO_SMALL);
    }
    ctx->state = SIGNATURE_CHECKED;
    output_buffer[0] = 0x90;
    output_buffer[1] = 0x00;
    return 2;
}