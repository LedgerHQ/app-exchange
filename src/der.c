#include "os.h"

static size_t asn1_get_encoded_length_size(size_t len) {
    if (len < 0x80) {
        return 1;
    }

    if (len < 0x100) {
        // 81 ..
        return 2;
    }

    if (len < 0x10000) {
        // 82 .. ..
        return 3;
    }

    return 0;
}

// return the length of an asn1 integer, aka '02' L V
size_t asn1_get_encoded_integer_size(uint8_t *val, size_t len) {
    size_t l0;

    while (len && (*val == 0)) {
        val++;
        len--;
    }

    if (len == 0) {
        len = 1;
    } else if (*val & 0x80u) {
        len++;
    }

    l0 = asn1_get_encoded_length_size(len);

    if (l0 == 0) {
        return 0;
    }

    return 1 + l0 + len;
}

static int asn1_insert_tag(uint8_t **p, const uint8_t *end, unsigned int tag) {
    if ((end - *p) < 1) {
        return 0;
    }

    **p = tag;
    (*p)++;

    return 1;
}

static int asn1_insert_len(uint8_t **p, const uint8_t *end, size_t len) {
    if (len < 0x80) {
        if ((end - *p) < 1) {
            return 0;
        }
        (*p)[0] = len & 0xFF;
        (*p) += 1;

        return 1;
    }

    if (len < 0x100) {
        if ((end - *p) < 2) {
            return 0;
        }

        (*p)[0] = 0x81u;
        (*p)[1] = len & 0xFF;
        (*p) += 2;

        return 2;
    }

    if (len < 0x10000) {
        if ((end - *p) < 3) {
            return 0;
        }

        (*p)[0] = 0x82u;
        (*p)[1] = (len >> 8) & 0xFF;
        (*p)[2] = len & 0xFF;
        (*p) += 3;

        return 3;
    }

    return 0;
}

static int asn1_insert_integer(uint8_t **p, const uint8_t *end, const uint8_t *val, size_t len) {
    while (len && (*val == 0)) {
        val++;
        len--;
    }

    if (!asn1_insert_tag(p, end, 0x02)) {
        return 0;
    }

    // special case for 0
    if (len == 0) {
        if ((end - *p) < 2) {
            return 0;
        }

        (*p)[0] = 0x01u;
        (*p)[1] = 0x00u;
        (*p) += 2;

        return 1;
    }

    // cont with len != 0, so val != 0
    if (!asn1_insert_len(p, end, len && (*val & 0x80) ? len + 1 : len)) {
        return 0;
    }

    if (len && (*val & 0x80)) {
        if ((end - *p) < 1) {
            return 0;
        }
        **p = 0;
        (*p)++;
    }

    if ((end - *p) < (int) len) {
        return 0;
    }

    os_memmove(*p, val, len);
    (*p) += len;

    return 1;
}

int encode_sig_der(uint8_t *sig, size_t sig_len, uint8_t *r, size_t r_len, uint8_t *s,
                   size_t s_len) {
    size_t l0, len;
    const uint8_t *sig_end = sig + sig_len;

    len = 0;

    l0 = asn1_get_encoded_integer_size(r, r_len);

    if (l0 == 0) {
        return 0;
    }

    len += l0;

    l0 = asn1_get_encoded_integer_size(s, s_len);

    if (l0 == 0) {
        return 0;
    }

    len += l0;

    if (!asn1_insert_tag(&sig, sig_end, 0x30) || !asn1_insert_len(&sig, sig_end, len) ||
        !asn1_insert_integer(&sig, sig_end, r, r_len) ||
        !asn1_insert_integer(&sig, sig_end, s, s_len)) {
        return 0;
    }

    return sig_len - (sig_end - sig);
}
