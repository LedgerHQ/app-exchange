#include "process_transaction.h"
#include "pb_decode.h"
#include "protocol.pb.h"
#include "swap_errors.h"
#include "reply_error.h"

int process_transaction(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, SendFunction send) {
    pb_istream_t stream = pb_istream_from_buffer(input_buffer, input_buffer_length);
    if (!pb_decode(&stream, ledger_swap_NewTransactionResponse_fields, &ctx->received_transaction)) {
        PRINTF("Error: Can't parse transaction protobuf");
        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }
    if (os_memcmp(ctx->device_tx_id, ctx->received_transaction.device_transaction_id, sizeof(ctx->device_tx_id)) != 0) {
        PRINTF("Error: Device transaction IDs doesn't match");
        return reply_error(ctx, WRONG_TRANSACTION_ID, send);
    }
    cx_hash_sha256(input_buffer, input_buffer_length, ctx->transaction_sha256_digest, sizeof(ctx->transaction_sha256_digest));
    unsigned char output_buffer[2] = {0x90, 0x00};
    if (send(output_buffer, 2) < 0) {
        PRINTF("Error: failed to send response");
        return -1;
    }
    ctx->state = TRANSACTION_RECIEVED;
    return 0;
}