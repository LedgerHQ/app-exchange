#ifndef _CHECK_TX_SIGNATURE_H_
#define _CHECK_TX_SIGNATURE_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int check_tx_signature(swap_app_context_t *ctx, const command_t *cmd, SendFunction send);

#endif  // _CHECK_TX_SIGNATURE_H_
