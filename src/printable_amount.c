#include "os.h"
#include <string.h>

static uint64_t uint64_from_BEarray(unsigned char *data, unsigned int len) {
    uint64_t result = 0;

    for (size_t i = 0; i < len; i++) {
        result <<= 8;
        result += data[i];
    }

    return result;
}

static int int64_to_str(char *data, int size, int64_t number) {
    char temp[] = "-9223372036854775808";

    char *ptr = temp;
    int64_t num = number;
    int sign = 1;

    if (number < 0) {
        sign = -1;
    }

    while (num != 0) {
        *ptr++ = '0' + (num % 10) * sign;
        num /= 10;
    }

    if (number < 0) {
        *ptr++ = '-';
    } else if (number == 0) {
        *ptr++ = '0';
    }

    int distance = (ptr - temp) + 1;

    if (size < distance) {
        return -1;
    }

    int index = 0;

    while (--ptr >= temp) {
        data[index++] = *ptr;
    }

    data[index] = '\0';

    return 0;
}

static int fpuint64_to_str(char *dst, size_t size, const uint64_t value, uint8_t decimals) {
    char buffer[30];

    if (int64_to_str(buffer, 30, value) < 0) {
        return -1;
    }

    size_t digits = strlen(buffer);

    if (digits <= decimals) {
        if (size <= 2 + decimals - digits) {
            return -1;
        }
        *dst++ = '0';
        *dst++ = '.';
        for (uint16_t i = 0; i < decimals - digits; i++, dst++) {
            *dst = '0';
        }
        size -= 2 + decimals - digits;
        strncpy(dst, buffer, size);
    } else {
        if (size <= digits + 1 + decimals) {
            return -1;
        }

        const size_t shift = digits - decimals;
        memcpy(dst, buffer, shift);
        dst[shift] = '.';
        strncpy(dst + shift + 1, buffer + shift, decimals);
    }

    return 0;
}

int get_fiat_printable_amount(unsigned char *amount_be, unsigned int amount_be_len,  //
                              unsigned int exponent,                                 //
                              char *printable_amount, unsigned int printable_amount_len) {
    uint64_t amount = uint64_from_BEarray(amount_be, amount_be_len);

    return fpuint64_to_str(printable_amount, printable_amount_len, amount, exponent);
}
