#include "unexpected_command.h"
#include "reply_error.h"
#include "swap_errors.h"

int unexpected_command(swap_app_context_t *ctx,                               //
                       unsigned char *input_buffer, int input_buffer_length,  //
                       SendFunction send) {
    return reply_error(ctx, INVALID_INSTRUCTION, send);
}
