#include "process_transaction.h"
#include "pb_decode.h"
#include "protocol.pb.h"
#include "errors.h"
#include "apdu_offsets.h"

int process_transaction(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length) {
    if (input_buffer_length < OFFSET_CDATA) {
        PRINTF("Error: Input buffer is too small");
        THROW(INCORRECT_COMMAND_DATA);
    }
    pb_istream_t stream = pb_istream_from_buffer(input_buffer + OFFSET_CDATA, input_buffer_length - OFFSET_CDATA);
    if (!pb_decode(&stream, ledger_swap_NewTransactionResponse_fields, &ctx->received_transaction)) {
        PRINTF("Error: Can't parse transaction protobuf");
        THROW(DESERIALIZATION_FAILED);
    }
    if (output_buffer_length < 2) {
        PRINTF("Output buffer is too small");
        THROW(OUTPUT_BUFFER_IS_TOO_SMALL);
    }
    cx_hash_sha256(input_buffer + OFFSET_CDATA, input_buffer_length - OFFSET_CDATA, ctx->transaction_sha256_digest, sizeof(ctx->transaction_sha256_digest));
    ctx->state = TRANSACTION_RECIEVED;
    output_buffer[0] = 0x90;
    output_buffer[1] = 0x00;
    return 2;
}