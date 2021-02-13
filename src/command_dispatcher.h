#ifndef _COMMAND_DISPATCHER_H_
#define _COMMAND_DISPATCHER_H_

#include "send_function.h"
#include "commands.h"
#include "swap_app_context.h"

int dispatch_command(swap_app_context_t *context, const command_t *cmd, SendFunction send);

#endif  //_COMMAND_DISPATCHER_H_
