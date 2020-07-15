#include "start_new_transaction.h"
#include "init.h"
#include "reply_error.h"

void create_device_tx_id(char *device_tx_id, unsigned int len) {
    for (unsigned int i = 0; i < len; ++i) {
        // device_tx_id[i] = (char)((int)'A' + cx_rng_u8() % 26);
        device_tx_id[i] = (char) ((int) 'A' + 42 % 26);  // No RNG
    }
}

int start_new_transaction(subcommand_e subcommand,                                        //
                          swap_app_context_t *ctx,                                        //
                          unsigned char *input_buffer, unsigned int input_buffer_length,  //
                          SendFunction send) {
    init_application_context(ctx);
    create_device_tx_id(ctx->device_transaction_id.swap, sizeof(ctx->device_transaction_id.swap));
    unsigned char output_buffer[sizeof(ctx->device_transaction_id.swap) + 2];
    os_memcpy(output_buffer, ctx->device_transaction_id.swap,
              sizeof(ctx->device_transaction_id.swap));
    output_buffer[sizeof(ctx->device_transaction_id.swap)] = 0x90;
    output_buffer[sizeof(ctx->device_transaction_id.swap) + 1] = 0x00;
    if (send(output_buffer, sizeof(output_buffer)) < 0) {
        PRINTF("Error: failed to send");
        return -1;
    }
    ctx->state = WAITING_TRANSACTION;
    return 0;
}
