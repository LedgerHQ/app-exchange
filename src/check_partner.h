#ifndef _CHECK_PARTNER_H_
#define _CHECK_PARTNER_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int check_partner(subcommand_e subcommand,                                        //
                  swap_app_context_t *ctx,                                        //
                  unsigned char *input_buffer, unsigned int input_buffer_length,  //
                  SendFunction send);

#endif  // _CHECK_PARTNER_H_