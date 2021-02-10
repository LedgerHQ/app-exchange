#ifndef _MENU_H_
#define _MENU_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "reply_error.h"
#include "commands.h"

void ux_init();

void ui_idle(void);

#define UX_SWAP          (1 << 0)
#define UX_SELL          (1 << 1)
#define UX_FLOATING_RATE (1 << 2)

typedef void (*UserChoiseCallback)();

void ui_validate_amounts(subcommand_e subcommand,  //
                         rate_e rate,
                         swap_app_context_t *ctx,  //
                         char *send_amount,        //
                         char *fees_amount,        //
                         SendFunction send);

#endif
