#ifndef _COMMAND_DISPATCHER_H_
#define _COMMAND_DISPATCHER_H_

#include "send_function.h"
#include "commands.h"
#include "swap_app_context.h"

int dispatch_command(command_e command, subcommand_e subcommand,             //
                     swap_app_context_t *context,                            //
                     unsigned char *input_buffer, unsigned int buffer_size,  //
                     SendFunction send);

#endif  //_COMMAND_DISPATCHER_H_