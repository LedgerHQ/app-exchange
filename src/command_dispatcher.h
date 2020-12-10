#ifndef _COMMAND_DISPATCHER_H_
#define _COMMAND_DISPATCHER_H_

#include "send_function.h"
#include "commands.h"
#include "swap_app_context.h"

int dispatch_command(command_e command,
                     subcommand_e subcommand,
                     swap_app_context_t *context,
                     const buf_t *input,
                     SendFunction send);

#endif  //_COMMAND_DISPATCHER_H_
