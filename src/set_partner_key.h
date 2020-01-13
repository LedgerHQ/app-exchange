#ifndef _SET_PARTNER_KEY_H_
#define _SET_PARTNER_KEY_H_

#include "swap_app_context.h"
#include "send_function.h"

int set_partner_key(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, SendFunction send);

#endif //_SET_PARTNER_KEY_H_