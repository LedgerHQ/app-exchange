#include <cx.h>

#include "start_new_transaction.h"
#include "init.h"
#include "io.h"

int start_new_transaction(const command_t *cmd) {
    // prepare size for device_transaction_id + 0x9000
    uint8_t output_buffer[sizeof(G_swap_ctx.device_transaction_id) + 2];
    size_t output_buffer_size = 0;

    init_application_context();

    if (cmd->subcommand == SWAP) {
        output_buffer_size = sizeof(G_swap_ctx.device_transaction_id.swap);

        for (unsigned int i = 0; i < output_buffer_size; ++i) {
#ifdef TESTING
            G_swap_ctx.device_transaction_id.swap[i] = (char) ((int) 'A' + 42 % 26);
#else
            G_swap_ctx.device_transaction_id.swap[i] = (char) ((int) 'A' + cx_rng_u8() % 26);
#endif
        }
    }

    if (cmd->subcommand == SELL || cmd->subcommand == FUND) {
        output_buffer_size = sizeof(G_swap_ctx.device_transaction_id.sell_fund);

#ifdef TESTING
        unsigned char tx_id[32] = {
            0x35, 0x0a, 0xea, 0x0c, 0x97, 0xf7, 0x47, 0xf1,  //
            0xd0, 0xf7, 0x60, 0x81, 0x46, 0x14, 0xa4, 0x75,  //
            0x23, 0x80, 0x1b, 0x1a, 0xeb, 0x7d, 0x0b, 0xcb,  //
            0xba, 0xa2, 0xa4, 0xf4, 0x6b, 0xf8, 0x18, 0x4b   //
        };
        memcpy(G_swap_ctx.device_transaction_id.sell_fund, tx_id, sizeof(tx_id));
#else
        cx_rng(G_swap_ctx.device_transaction_id.sell_fund, output_buffer_size);
#endif
    }

    memcpy(output_buffer, &G_swap_ctx.device_transaction_id, output_buffer_size);

    // TODO: add extra sw args for send() and skip status word set in each caller
    output_buffer[output_buffer_size] = 0x90;
    output_buffer[output_buffer_size + 1] = 0x00;

    output_buffer_size += 2;

    if (send_apdu(output_buffer, output_buffer_size) < 0) {
        PRINTF("Error: failed to send");
        return -1;
    }

    G_swap_ctx.state = WAITING_TRANSACTION;
    G_swap_ctx.subcommand = cmd->subcommand;
    G_swap_ctx.rate = cmd->rate;

    return 0;
}
