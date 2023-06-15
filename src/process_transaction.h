#ifndef _PROCESS_TRANSACTION_H_
#define _PROCESS_TRANSACTION_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int process_transaction(swap_app_context_t *ctx, const command_t *cmd, SendFunction send);

#endif  // _PROCESS_TRANSACTION_H_
