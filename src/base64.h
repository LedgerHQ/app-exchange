#ifndef _BASE64_H_
#define _BASE64_H_

#include <stddef.h>

int base64_decode(unsigned char *bufplain, size_t maxsize, const unsigned char *bufcoded, size_t len);

#endif  // _BASE64_H_
