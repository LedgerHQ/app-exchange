#ifndef _CHECK_TO_ADDRESS_H_
#define _CHECK_TO_ADDRESS_H_

#include "swap_app_context.h"
#include "send_function.h"

int check_payout_address(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    SendFunction send);

#endif // _CHECK_TO_ADDRESS_H_