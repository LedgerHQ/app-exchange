#ifndef _UNEXPECTED_COMMAND_H_
#define _UNEXPECTED_COMMAND_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int unexpected_command(swap_app_context_t *ctx, const command_t *cmd, SendFunction send);

#endif  //_UNEXPECTED_COMMAND_H_
