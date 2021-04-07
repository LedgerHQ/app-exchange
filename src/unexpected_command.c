#include "unexpected_command.h"
#include "reply_error.h"
#include "swap_errors.h"

int unexpected_command(swap_app_context_t *ctx, const command_t *cmd, SendFunction send) {
    return reply_error(ctx, INVALID_INSTRUCTION, send);
}
