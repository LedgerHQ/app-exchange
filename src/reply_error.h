#ifndef _REPLY_ERROR_H_
#define _REPLY_ERROR_H_

#include "swap_app_context.h"
#include "send_function.h"
#include "swap_errors.h"

// Send a error message, change the state to INITIAL
// return negative number in case of something go wrong (send operation for example)
int reply_error(swap_app_context_t* ctx, swap_error_e error, SendFunction send);

#endif // _REPLY_ERROR_H_