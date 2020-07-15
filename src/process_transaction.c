#include "process_transaction.h"
#include "pb_decode.h"
#include "protocol.pb.h"
#include "swap_errors.h"
#include "reply_error.h"

void to_uppercase(char *str, unsigned char size) {
    for (unsigned char i = 0; i < size && str[i] != 0; i++) {
        str[i] = str[i] >= 'a' ? str[i] - ('a' - 'A') : str[i];
    }
}

int process_transaction(subcommand_e subcommand,                                        //
                        swap_app_context_t *ctx,                                        //
                        unsigned char *input_buffer, unsigned int input_buffer_length,  //
                        SendFunction send) {
    if (input_buffer_length < 1) {
        PRINTF("Error: Can't parse process_transaction message, length should be more then 1");
        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }
    unsigned char proto_length = input_buffer[0];
    pb_istream_t stream = pb_istream_from_buffer(input_buffer + 1, proto_length);
    if (!pb_decode(&stream, ledger_swap_NewTransactionResponse_fields,
                   &ctx->received_transaction)) {
        PRINTF("Error: Can't parse transaction protobuf");
        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }
    if (os_memcmp(ctx->device_transaction_id.swap, ctx->received_transaction.device_transaction_id,
                  sizeof(ctx->device_transaction_id.swap)) != 0) {
        PRINTF("Error: Device transaction IDs doesn't match");
        return reply_error(ctx, WRONG_TRANSACTION_ID, send);
    }
    cx_hash_sha256(input_buffer + 1, proto_length, ctx->sha256_digest, sizeof(ctx->sha256_digest));
    if (input_buffer_length < 1 + proto_length + 1) {
        PRINTF("Error: Can't parse process_transaction message, should include fee");
        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }
    ctx->transaction_fee_length = input_buffer[1 + proto_length];
    if (ctx->transaction_fee_length > sizeof(ctx->transaction_fee)) {
        PRINTF("Error: Transaction fee is to long");
        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }
    if (input_buffer_length < 1 + proto_length + 1 + ctx->transaction_fee_length) {
        PRINTF("Error: Input buffer is too small");
        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }
    to_uppercase(ctx->received_transaction.currency_from,
                 sizeof(ctx->received_transaction.currency_from));
    to_uppercase(ctx->received_transaction.currency_to,
                 sizeof(ctx->received_transaction.currency_to));
    os_memset(ctx->transaction_fee, 0, sizeof(ctx->transaction_fee));
    os_memcpy(ctx->transaction_fee, input_buffer + 1 + proto_length + 1,
              ctx->transaction_fee_length);
    PRINTF("Transaction fees BE = %.*H\n", ctx->transaction_fee_length, ctx->transaction_fee);
    unsigned char output_buffer[2] = {0x90, 0x00};
    if (send(output_buffer, 2) < 0) {
        PRINTF("Error: failed to send response");
        return -1;
    }
    ctx->state = TRANSACTION_RECIEVED;
    return 0;
}