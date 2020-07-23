#ifndef _DER_H_
#define _DER_H_

#include "os.h"

size_t asn1_get_encoded_integer_size(uint8_t *val, size_t len);

int encode_sig_der(uint8_t *sig, size_t sig_len, uint8_t *r, size_t r_len, uint8_t *s,
                   size_t s_len);

#endif  // _DER_H_
