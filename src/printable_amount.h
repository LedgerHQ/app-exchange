#ifndef _PRINTABLE_AMOUNT_H_
#define _PRINTABLE_AMOUNT_H_

#include "os.h"

int get_fiat_printable_amount(unsigned char *amount_be, unsigned int amount_be_len,  //
                              unsigned int exponent,                                 //
                              char *printable_amount, unsigned int printable_amount_len);

#endif  // _PRINTABLE_AMOUNT_H_
