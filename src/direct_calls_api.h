#pragma once

#include "commands.h"

#ifdef DIRECT_CALLS_API
int direct_check_address(const command_t *cmd);
int direct_format_amount(const command_t *cmd);
#endif  // DIRECT_CALLS_API
