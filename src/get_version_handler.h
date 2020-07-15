#ifndef _GET_VERSION_HANDLER_
#define _GET_VERSION_HANDLER_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int get_version_handler(subcommand_e subcommand,                                        //
                        swap_app_context_t *ctx,                                        //
                        unsigned char *input_buffer, unsigned int input_buffer_length,  //
                        SendFunction send);

#endif