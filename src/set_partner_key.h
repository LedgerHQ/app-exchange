#ifndef _SET_PARTNER_KEY_H_
#define _SET_PARTNER_KEY_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int set_partner_key(subcommand_e subcommand,
                    swap_app_context_t *ctx,
                    const buf_t *input,
                    SendFunction send);

#endif  //_SET_PARTNER_KEY_H_
