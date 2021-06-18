#include "start_new_transaction.h"
#include "init.h"
#include "reply_error.h"

int start_new_transaction(swap_app_context_t *ctx, const command_t *cmd, SendFunction send) {
    unsigned char output_buffer[sizeof(ctx->device_transaction_id) + 2];
    unsigned int output_buffer_size = 0;

    init_application_context(ctx);

    if (cmd->subcommand == SWAP) {
        output_buffer_size = sizeof(ctx->device_transaction_id.swap);

        for (unsigned int i = 0; i < output_buffer_size; ++i) {
#ifdef TESTING
            ctx->device_transaction_id.swap[i] = (char) ((int) 'A' + 42 % 26);
            // uint8_t replay_id[] = {0x61, 0x71, 0x65, 0x75, 0x6c, 0x63, 0x68, 0x71, 0x65, 0x6b};
            // memcpy(ctx->device_transaction_id.swap, replay_id, sizeof(replay_id));
#else
            ctx->device_transaction_id.swap[i] = (char) ((int) 'A' + cx_rng_u8() % 26);
#endif
        }
    }

    if (cmd->subcommand == SELL) {
        output_buffer_size = sizeof(ctx->device_transaction_id.sell);

#ifdef TESTING
        unsigned char tx_id[32] = {
            0x35, 0x0a, 0xea, 0x0c, 0x97, 0xf7, 0x47, 0xf1,  //
            0xd0, 0xf7, 0x60, 0x81, 0x46, 0x14, 0xa4, 0x75,  //
            0x23, 0x80, 0x1b, 0x1a, 0xeb, 0x7d, 0x0b, 0xcb,  //
            0xba, 0xa2, 0xa4, 0xf4, 0x6b, 0xf8, 0x18, 0x4b   //
        };

        os_memmove(ctx->device_transaction_id.sell, tx_id, sizeof(tx_id));
#else
        cx_rng(ctx->device_transaction_id.sell, output_buffer_size);
#endif
    }

    os_memcpy(output_buffer, &ctx->device_transaction_id, output_buffer_size);

    // TODO: add extra sw args for send() and skip status word set in each caller
    output_buffer[output_buffer_size] = 0x90;
    output_buffer[output_buffer_size + 1] = 0x00;

    output_buffer_size += 2;

    if (send(output_buffer, output_buffer_size) < 0) {
        PRINTF("Error: failed to send");
        return -1;
    }

    ctx->state = WAITING_TRANSACTION;
    ctx->subcommand = cmd->subcommand;

    return 0;
}
