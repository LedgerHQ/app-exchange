#include "unexpected_command.h"
#include "os.h"
#include "errors.h"

int unexpected_command(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length) {
    os_memset((void*)&ctx, 0, sizeof(ctx));
    ctx->state = INITIAL_STATE;
    if (output_buffer_length < 2) {
        PRINTF("Output buffer is too small");
        THROW(OUTPUT_BUFFER_IS_TOO_SMALL);
    }
    output_buffer[0] = 0x6D;
    output_buffer[1] = 0x00;
    return 2;
}
