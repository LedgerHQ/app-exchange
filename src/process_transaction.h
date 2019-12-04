#ifndef _PROCESS_TRANSACTION_H_ 
#define _PROCESS_TRANSACTION_H_ 

#include "swap_app_context.h"

int process_transaction(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length);

#endif // _PROCESS_TRANSACTION_H_ 