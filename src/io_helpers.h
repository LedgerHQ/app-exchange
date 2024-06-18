#pragma once

#include <stdint.h>

#include "ux.h"
#include "os_io_seproxyhal.h"
#include "swap_errors.h"

int reply_error(swap_error_e error);
int instant_reply_error(swap_error_e error);

int reply_success(void);
int instant_reply_success(void);
