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

int strcmp_non_zero(char* str1, unsigned char str1_buffer_size, char* str2, unsigned char str2_buffer_size) {
    unsigned char len1 = strnlen(str1, str1_buffer_size);
    unsigned char len2 = strnlen(str2, str2_buffer_size);
    int res = strncmp(str1, str2, len1 < len2 ? len1 : len2);
    if (res != 0)
        return res;
    if (len1 == len2)
        return 0;
    return len1 < len2;
}