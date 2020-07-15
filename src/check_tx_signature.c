#include "check_tx_signature.h"
#include "os.h"
#include "globals.h"
#include "swap_errors.h"
#include "reply_error.h"

// This function receive transaction signature
// Input should be in the form of DER serialized signature
// the length should be CURVE_SIZE_BYTES * 2 + 6 (DER encoding)
int check_tx_signature(subcommand_e subcommand,                                        //
                       swap_app_context_t *ctx,                                        //
                       unsigned char *input_buffer, unsigned int input_buffer_length,  //
                       SendFunction send) {
    if (input_buffer_length < MIN_DER_SIGNATURE_LENGTH ||
        input_buffer_length > MAX_DER_SIGNATURE_LENGTH ||
        input_buffer[1] + 2 != input_buffer_length) {
        PRINTF("Error: Input buffer length don't correspond to DER length");
        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }
    if (cx_ecdsa_verify(&ctx->partner.public_key, CX_LAST, CX_SHA256, ctx->sha256_digest,
                        CURVE_SIZE_BYTES, input_buffer, input_buffer_length) == 0) {
        PRINTF("Error: Failed to verify signature of received transaction");
        return reply_error(ctx, SIGN_VERIFICATION_FAIL, send);
    }
    unsigned char output_buffer[2] = {0x90, 0x00};
    if (send(output_buffer, 2) < 0) {
        PRINTF("Error: Can't send message");
        return -1;
    }
    ctx->state = SIGNATURE_CHECKED;
    return 0;
}