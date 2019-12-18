#include "os.h"
#include "cx.h"
#include <stdbool.h>
#include <stdlib.h>
#include "utils.h"
#include "menu.h"

int addResponseCode(unsigned char* buffer, int buffer_length, int response_code) {
    if (buffer_length < 2) {
        PRINTF("Output buffer is too small");
        THROW(0x6000);
    }
    buffer[0] = (response_code >> 8) & 0xFF;
    buffer[1] = response_code & 0xFF;
    return 2;
}