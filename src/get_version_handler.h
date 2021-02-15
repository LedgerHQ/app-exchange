#ifndef _GET_VERSION_HANDLER_
#define _GET_VERSION_HANDLER_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int get_version_handler(swap_app_context_t *ctx, const command_t *cmd, SendFunction send);

#endif
