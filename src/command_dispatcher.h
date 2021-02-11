#ifndef _COMMAND_DISPATCHER_H_
#define _COMMAND_DISPATCHER_H_

#include "send_function.h"
#include "commands.h"
#include "swap_app_context.h"

int dispatch_command(command_e command,
                     rate_e P1,
                     subcommand_e P2,
                     swap_app_context_t *context,
                     const buf_t *input,
                     SendFunction send);

#endif  //_COMMAND_DISPATCHER_H_
