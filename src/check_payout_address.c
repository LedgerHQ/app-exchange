#include "check_payout_address.h"
#include "os.h"
#include "errors.h"
#include "globals.h"
#include "check_address.h"

// 1 byte length X of "to" currency configuration 
// X bytes "to" currency configuration
// 70 bytes DER serialized signature
// 1 byte length Y of address paramaters (path, version etc.)
// Y bytes of address parameters
int check_payout_address(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    unsigned char* output_buffer, int output_buffer_length) {
    if (input_buffer_length < 72) {
        PRINTF("Error: Input buffer is too small to contain correct CHECK_PAYOUT_ADDRESS message");
        THROW(INCORRECT_COMMAND_DATA);
    }
    // parse message
    unsigned char config_length = input_buffer[0];
    if (input_buffer_length < 2 + DER_SIGNATURE_LENGTH + config_length) {
        PRINTF("Error: Input buffer is too small to contain correct CHECK_PAYOUT_ADDRESS message");
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
        ctx->received_transaction.currency_to,
        ctx->received_transaction.payout_address,
        ctx->received_transaction.payout_extra_id)) {
        PRINTF("Error: Payout address validation failed");
        THROW(INVALID_ADDRESS);
    }
    PRINTF("Payout address validated");
    ctx->state = TO_ADDR_CHECKED;
    output_buffer[0] = 0x90;
    output_buffer[1] = 0x00;
    return 2;
}
