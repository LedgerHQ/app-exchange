#include "start_new_transaction.h"
#include "init.h"
#include "reply_error.h"

int start_new_transaction(subcommand_e subcommand,                                        //
                          swap_app_context_t *ctx,                                        //
                          unsigned char *input_buffer, unsigned int input_buffer_length,  //
                          SendFunction send) {
    unsigned char output_buffer[sizeof(ctx->device_transaction_id) + 2];
    unsigned int output_buffer_size = 0;

    init_application_context(ctx);

    if (subcommand == SWAP) {
        output_buffer_size = sizeof(ctx->device_transaction_id.swap);

        for (unsigned int i = 0; i < output_buffer_size; ++i) {
#ifdef OLD_TEST_PUBLIC_KEY
            ctx->device_transaction_id.swap[i] = (char) ((int) 'A' + 42 % 26);
#else
            ctx->device_transaction_id.swap[i] = (char) ((int) 'A' + cx_rng_u8() % 26);
#endif
        }
    }

    if (subcommand == SELL) {
        output_buffer_size = sizeof(ctx->device_transaction_id.sell);

#ifdef OLD_TEST_PUBLIC_KEY
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

    return 0;
}
