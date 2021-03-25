#ifndef _START_NEW_TRANSACTION_H_
#define _START_NEW_TRANSACTION_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int start_new_transaction(swap_app_context_t *ctx, const command_t *cmd, SendFunction send);

#endif  //_START_NEW_TRANSACTION_H_
