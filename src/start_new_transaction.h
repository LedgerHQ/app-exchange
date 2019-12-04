#ifndef _START_NEW_TRANSACTION_H
#define _START_NEW_TRANSACTION_H

#include "swap_app_context.h"

int start_new_transaction(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length);

#endif //_START_NEW_TRANSACTION_H