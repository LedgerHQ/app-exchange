#ifndef _CHECK_TX_SIGNATURE_H_
#define _CHECK_TX_SIGNATURE_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int check_tx_signature(subcommand_e subcommand,
                       swap_app_context_t *ctx,
                       const buf_t *input,
                       SendFunction send);

#endif  // _CHECK_TX_SIGNATURE_H_
