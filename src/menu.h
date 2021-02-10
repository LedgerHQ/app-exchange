#ifndef _MENU_H_
#define _MENU_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "reply_error.h"
#include "commands.h"

void ux_init();

void ui_idle(void);

typedef void (*UserChoiseCallback)();

void ui_validate_amounts(rate_e P1,  //
                         subcommand_e P2,
                         swap_app_context_t *ctx,  //
                         char *send_amount,        //
                         char *fees_amount,        //
                         SendFunction send);

#endif
