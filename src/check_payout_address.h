#ifndef _CHECK_TO_ADDRESS_H_
#define _CHECK_TO_ADDRESS_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int check_payout_address(rate_e P1,
                         subcommand_e P2,
                         swap_app_context_t *ctx,
                         const buf_t *input,
                         SendFunction send);

#endif  // _CHECK_TO_ADDRESS_H_
