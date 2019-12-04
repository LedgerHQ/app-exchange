#include "get_version_handler.h"
#include "os.h"
#include "errors.h"

int get_version_handler(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length) {
    if (output_buffer_length < 5) {
        PRINTF("Output buffer is too small");
        THROW(OUTPUT_BUFFER_IS_TOO_SMALL);
    }
    output_buffer[0] = 1;
    output_buffer[1] = 2;
    output_buffer[2] = 3;
    output_buffer[3] = 0x90;
    output_buffer[4] = 0x00;
    return 5;
}
