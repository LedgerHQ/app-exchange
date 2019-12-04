#ifndef _CHECK_SIGNATURE_H_ 
#define _CHECK_SIGNATURE_H_  

#include "swap_app_context.h"

int check_signature(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length);

#endif // _CHECK_SIGNATURE_H_ 