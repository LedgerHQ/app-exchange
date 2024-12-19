#include "get_version_handler.h"
#include "swap_errors.h"
#include "buffer.h"
#include "io.h"

int get_version_handler(void) {
    unsigned char output_buffer[3];
    output_buffer[0] = MAJOR_VERSION;
    output_buffer[1] = MINOR_VERSION;
    output_buffer[2] = PATCH_VERSION;

    buffer_t output;
    output.ptr = output_buffer;
    output.size = 3;
    output.offset = 0;

    if (io_send_response_buffers(&output, 1, SUCCESS) < 0) {
        return -1;
    }
    return 0;
}
