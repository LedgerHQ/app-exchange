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

static char *int64_to_str(char *data, int size, int64_t number) {
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
        return "Size too small";
    }

    int index = 0;

    while (--ptr >= temp) {
        data[index++] = *ptr;
    }

    data[index] = '\0';

    return NULL;
}

static void fpuint64_to_str(char *dst, const uint64_t value, uint8_t decimals) {
    char buffer[30];

    int64_to_str(buffer, 30, value);
    size_t digits = strlen(buffer);

    if (digits <= decimals) {
        *dst++ = '0';
        *dst++ = '.';
        for (uint16_t i = 0; i < decimals - digits; i++, dst++) {
            *dst = '0';
        }
        strcpy(dst, buffer);
    } else {
        strcpy(dst, buffer);
        const size_t shift = digits - decimals;
        dst = dst + shift;
        *dst++ = '.';

        char *p = buffer + shift;
        strcpy(dst, p);
    }
}

int get_fiat_printable_amount(unsigned char *amount_be, unsigned int amount_be_len,  //
                              unsigned int exponent,                                 //
                              char *printable_amount, unsigned int printable_amount_len) {
    uint64_t amount = uint64_from_BEarray(amount_be, amount_be_len);

    fpuint64_to_str(printable_amount, amount, exponent);

    return 0;
}
