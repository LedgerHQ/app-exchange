#ifndef _PROCESS_TRANSACTION_H_ 
#define _PROCESS_TRANSACTION_H_ 

#include "swap_app_context.h"
#include "send_function.h"

int process_transaction(
    swap_app_context_t* ctx,
    unsigned char* input_buffer, int input_buffer_length,
    SendFunction send);

#endif // _PROCESS_TRANSACTION_H_ 