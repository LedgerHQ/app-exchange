#include "reply_error.h"
#include "os.h"
#include "swap_errors.h"
#include "init.h"

int reply_error(swap_app_context_t* ctx, swap_error_e error, SendFunction send) {
    init_application_context(ctx);
    unsigned char output_buffer[2] = {(error >> 8) & 0xFF, error & 0xFF};
    return send(output_buffer, 2);
}