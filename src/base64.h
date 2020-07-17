#ifndef _BASE64_H_
#define _BASE64_H_

int base64_decode_len(int len);

void base64_decode(char *bufplain, const char *bufcoded, int len);

#endif  // _BASE64_H_
