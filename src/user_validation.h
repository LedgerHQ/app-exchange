#ifndef _USER_VALIDATION_H_
#define _USER_VALIDATION_H_

#include "swap_app_context.h"
#include "send_function.h"

int user_validation(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, SendFunction send);

#endif // _USER_VALIDATION_H_