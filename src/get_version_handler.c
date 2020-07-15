#include "get_version_handler.h"

int get_version_handler(subcommand_e subcommand,                                        //
                        swap_app_context_t *ctx,                                        //
                        unsigned char *input_buffer, unsigned int input_buffer_length,  //
                        SendFunction send) {
    unsigned char output_buffer[5];
    output_buffer[0] = LEDGER_MAJOR_VERSION;
    output_buffer[1] = LEDGER_MINOR_VERSION;
    output_buffer[2] = LEDGER_PATCH_VERSION;
    output_buffer[3] = 0x90;
    output_buffer[4] = 0x00;
    if (send(output_buffer, 5) < 0) {
        return -1;
    }
    return 0;
}
