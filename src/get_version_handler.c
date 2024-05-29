#include "get_version_handler.h"
#include "io.h"

int get_version_handler(void) {
    unsigned char output_buffer[5];
    output_buffer[0] = MAJOR_VERSION;
    output_buffer[1] = MINOR_VERSION;
    output_buffer[2] = PATCH_VERSION;
    output_buffer[3] = 0x90;
    output_buffer[4] = 0x00;
    if (send_apdu(output_buffer, 5) < 0) {
        return -1;
    }
    return 0;
}
