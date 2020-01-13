#include "der_serialization.h"
#include "os.h"

unsigned char der_serialize(
    unsigned char* R, unsigned char r_length,
    unsigned char* S, unsigned char s_length,
    unsigned char* der, unsigned char output_buffer_size) {
    //                        30  L   02  Lr  r          02  Ls  s
    unsigned int der_length = 1 + 1 + 1 + 1 + r_length + 1 + 1 + s_length;
    if (der_length > output_buffer_size) {
        PRINTF("Error: Output buffer for DER is too small");
        return -1;
    }
    unsigned char off = 0;
    der[off++] = 30;
    der[off++] = der_length - 2; // do not count first two bytes [30, L]
    der[off++] = 2;
    der[off++] = r_length;
    os_memcpy(der + off, R, r_length);
    off += r_length;
    der[off++] = 2;
    der[off++] = s_length;
    os_memcpy(der + off, S, s_length);
    off += s_length;
    return off;
}
