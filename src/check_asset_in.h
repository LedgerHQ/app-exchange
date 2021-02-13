#ifndef _CHECK_ASSET_IN_H_
#define _CHECK_ASSET_IN_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "commands.h"

int check_asset_in(swap_app_context_t *ctx, const command_t *cmd, SendFunction send);

#endif  // _CHECK_ASSET_IN_H_
