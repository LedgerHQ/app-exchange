#ifndef _START_NEW_TRANSACTION_H_
#define _START_NEW_TRANSACTION_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int start_new_transaction(subcommand_e subcommand,                                        //
                          swap_app_context_t *ctx,                                        //
                          unsigned char *input_buffer, unsigned int input_buffer_length,  //
                          SendFunction send);

#endif  //_START_NEW_TRANSACTION_H_
