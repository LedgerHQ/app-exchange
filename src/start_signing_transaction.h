#ifndef _START_SIGNING_TRANSACTION_H_
#define _START_SIGNING_TRANSACTION_H_

#include "send_function.h"
#include "swap_app_context.h"
#include "commands.h"

int start_signing_transaction(subcommand_e subcommand,                                        //
                              swap_app_context_t *ctx,                                        //
                              unsigned char *input_buffer, unsigned int input_buffer_length,  //
                              SendFunction send);

#endif  //_START_SIGNING_TRANSACTION_H_