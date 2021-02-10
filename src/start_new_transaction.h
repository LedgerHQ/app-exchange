#ifndef _START_NEW_TRANSACTION_H_
#define _START_NEW_TRANSACTION_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int start_new_transaction(rate_e P1,
                          subcommand_e P2,
                          swap_app_context_t *ctx,
                          const buf_t *input,
                          SendFunction send);

#endif  //_START_NEW_TRANSACTION_H_
