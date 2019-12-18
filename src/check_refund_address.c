#include "check_refund_address.h"
#include "os.h"
#include "globals.h"
#include "check_address.h"
#include "user_validate_amounts.h"
#include "errors.h"
#include "get_printable_amount.h"

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
        ctx->received_transaction.refund_address,
        ctx->received_transaction.refund_extra_id)) {
        PRINTF("Error: Refund address validation failed");
        THROW(INVALID_ADDRESS);
    }
    char printable_send_amount[30] = {0};
    char printable_get_amount[30] = {0};
    get_printable_amount(
        input_buffer + 1,
        config_length,
        ctx->received_transaction.currency_from,
        ctx->received_transaction.amount_to_provider.bytes,
        ctx->received_transaction.amount_to_provider.size,
        printable_send_amount,
        sizeof(printable_send_amount));
    get_printable_amount(
        input_buffer + 1,
        config_length,
        ctx->received_transaction.currency_to,
        ctx->received_transaction.amount_to_wallet.bytes,
        ctx->received_transaction.amount_to_wallet.size,
        printable_get_amount,
        sizeof(printable_get_amount));

    if (!user_validate_amounts(
        printable_send_amount,
        printable_get_amount,
        "Changelly.com")) {
        PRINTF("Error: User refused transaction");
        THROW(USER_REFUSED);
    }
}