#ifndef _CHECK_REFUND_ADDRESS_H_
#define _CHECK_REFUND_ADDRESS_H_

#include "swap_app_context.h"

int check_refund_address(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    unsigned char* output_buffer, int output_buffer_length);

#endif // _CHECK_REFUND_ADDRESS_H_