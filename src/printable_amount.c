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

// Convert an unsigned 64-bit integer to its decimal string representation.
// Uses a temporary buffer sized for the largest uint64 value ("18446744073709551615").
// Digits are extracted in reverse order (least significant first), then copied
// back into `data` in the correct order.
// Returns 0 on success, -1 if `size` is too small to hold the result.
static int uint64_to_str(char *data, int size, uint64_t number) {
    // Temporary buffer large enough for max uint64_t decimal representation
    char temp[] = "18446744073709551615";

    char *ptr = temp;
    uint64_t num = number;

    // Extract digits in reverse order (units first)
    while (num != 0) {
        *ptr++ = '0' + (num % 10);
        num /= 10;
    }

    if (number == 0) {
        *ptr++ = '0';
    }

    // +1 for null terminator
    int distance = (ptr - temp) + 1;

    if (size < distance) {
        return -1;
    }

    // Copy digits in correct order (most significant first)
    int index = 0;

    while (--ptr >= temp) {
        data[index++] = *ptr;
    }

    data[index] = '\0';

    return 0;
}

static int fpuint64_to_str(char *dst, size_t size, const uint64_t value, uint8_t decimals) {
    char buffer[30];

    if (uint64_to_str(buffer, 30, value) < 0) {
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

int get_fiat_printable_amount(unsigned char *amount_be,
                              unsigned int amount_be_len,  //
                              unsigned int exponent,       //
                              char *printable_amount,
                              unsigned int printable_amount_len) {
    // Reject coefficient that doesn't fit in uint64_t
    if (amount_be_len > sizeof(uint64_t)) {
        PRINTF("Error: coefficient length %u exceeds 8 bytes\n", amount_be_len);
        return -1;
    }

    // Reject exponent that doesn't fit in uint8_t
    if (exponent > UINT8_MAX) {
        PRINTF("Error: exponent %u exceeds maximum %u\n", exponent, UINT8_MAX);
        return -1;
    }

    uint64_t amount = uint64_from_BEarray(amount_be, amount_be_len);

    int ret = fpuint64_to_str(printable_amount, printable_amount_len, amount, exponent);

    if (ret == 0) {
        PRINTF("get_fiat_printable_amount: formatted result='%s'\n", printable_amount);
    }

    return ret;
}
