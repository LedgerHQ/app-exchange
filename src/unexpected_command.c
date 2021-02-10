#include "unexpected_command.h"
#include "reply_error.h"
#include "swap_errors.h"

int unexpected_command(rate_e P1, swap_app_context_t *ctx, const buf_t *input, SendFunction send) {
    return reply_error(ctx, INVALID_INSTRUCTION, send);
}
