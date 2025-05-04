#include <cx.h>

#include "start_new_transaction.h"
#include "init.h"
#include "io.h"
#include "io_helpers.h"
#include "swap_errors.h"
#include "globals.h"
#include "menu.h"
#include "buffer.h"

int start_new_transaction(const command_t *cmd) {
    buffer_t output;

    // Force a UI reset if we are currently displaying a modal
    if (G_swap_ctx.state == WAITING_SIGNING) {
        PRINTF("Dismissing the modal and forcing the main menu\n");
        ui_idle();
    }

    memset(&G_swap_ctx, 0, sizeof(G_swap_ctx));
    G_swap_ctx.state = INITIAL_STATE;

    // Legacy swap flow : 10 char 'string' (not '\0' terminated)
    if (cmd->subcommand == SWAP) {
        output.ptr = (uint8_t *) G_swap_ctx.device_transaction_id.swap;
        output.size = sizeof(G_swap_ctx.device_transaction_id.swap);
        output.offset = 0;

        for (unsigned int i = 0; i < output.size; ++i) {
#ifdef TESTING
            G_swap_ctx.device_transaction_id.swap[i] = (char) ((int) 'A' + 42 % 26);
#else
            G_swap_ctx.device_transaction_id.swap[i] = (char) ((int) 'A' + cx_rng_u8() % 26);
#endif
        }
    } else {
        // All other flows : 32 bytes
        output.ptr = G_swap_ctx.device_transaction_id.unified;
        output.size = sizeof(G_swap_ctx.device_transaction_id.unified);
        output.offset = 0;

#ifdef TESTING
        unsigned char tx_id[32] = {
            0x35, 0x0a, 0xea, 0x0c, 0x97, 0xf7, 0x47, 0xf1,  //
            0xd0, 0xf7, 0x60, 0x81, 0x46, 0x14, 0xa4, 0x75,  //
            0x23, 0x80, 0x1b, 0x1a, 0xeb, 0x7d, 0x0b, 0xcb,  //
            0xba, 0xa2, 0xa4, 0xf4, 0x6b, 0xf8, 0x18, 0x4b   //
        };
        memcpy(G_swap_ctx.device_transaction_id.unified, tx_id, sizeof(tx_id));
#else
        cx_rng(G_swap_ctx.device_transaction_id.unified, output.size);
#endif
    }

    if (io_send_response_buffers(&output, 1, SUCCESS) < 0) {
        PRINTF("Error: failed to send\n");
        return -1;
    }

    G_swap_ctx.state = WAITING_TRANSACTION;
    G_swap_ctx.subcommand = cmd->subcommand;

    return 0;
}
