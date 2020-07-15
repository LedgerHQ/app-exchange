#ifndef _PROCESS_TRANSACTION_H_
#define _PROCESS_TRANSACTION_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int process_transaction(subcommand_e subcommand,                                        //
                        swap_app_context_t *ctx,                                        //
                        unsigned char *input_buffer, unsigned int input_buffer_length,  //
                        SendFunction send);

#endif  // _PROCESS_TRANSACTION_H_