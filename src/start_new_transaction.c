#include "start_new_transaction.h"
#include "errors.h"

void create_device_tx_id(char *device_tx_id, unsigned int len) {
    for (unsigned int i = 0; i < len; ++i) {
        device_tx_id[i] = (char)((int)'A' + cx_rng_u8() % 26);
    }
}

int start_new_transaction(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length) {
    if (output_buffer_length < 12) {
        PRINTF("Output buffer is too small");
        THROW(OUTPUT_BUFFER_IS_TOO_SMALL);
    }
    create_device_tx_id(ctx->device_tx_id, sizeof(ctx->device_tx_id));
    os_memset((void*)&ctx, 0, sizeof(ctx));
    ctx->state = WAITING_TRANSACTION;
    PRINTF("New transaction id %10s\n", ctx->device_tx_id);
    os_memcpy(output_buffer, ctx->device_tx_id, sizeof(ctx->device_tx_id));
    int output_length = sizeof(ctx->device_tx_id);
    output_buffer[output_length + sizeof(ctx->device_tx_id)] = 0x90;
    output_buffer[output_length + sizeof(ctx->device_tx_id) + 1] = 0x00;
    return output_length + 2;
}

