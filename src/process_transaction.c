#include "process_transaction.h"
#include "pb_decode.h"
#include "protocol.pb.h"
#include "errors.h"

int process_transaction(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length) {
    pb_istream_t stream = pb_istream_from_buffer(input_buffer, input_buffer_length);
    if (!pb_decode(&stream, ledger_swap_NewTransactionResponse_fields, &ctx->received_transaction)) {
        PRINTF("Error: Can't parse transaction protobuf");
        THROW(DESERIALIZATION_FAILED);
    }
    if (os_memcmp(ctx->device_tx_id, ctx->received_transaction.device_transaction_id, sizeof(ctx->device_tx_id)) != 0) {
        PRINTF("Error: Device transaction IDs doesn't match");
        THROW(WRONG_TRANSACTION_ID);
    }
    if (output_buffer_length < 2) {
        PRINTF("Error: Output buffer is too small");
        THROW(OUTPUT_BUFFER_IS_TOO_SMALL);
    }
    cx_hash_sha256(input_buffer, input_buffer_length, ctx->transaction_sha256_digest, sizeof(ctx->transaction_sha256_digest));
    ctx->state = TRANSACTION_RECIEVED;
    output_buffer[0] = 0x90;
    output_buffer[1] = 0x00;
    return 2;
}