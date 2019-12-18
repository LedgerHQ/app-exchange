#ifndef _GET_PRINTABLE_AMOUN_H_
#define _GET_PRINTABLE_AMOUN_H_

int get_printable_amount(
    unsigned char* coin_config,
    unsigned char coin_config_length,
    char * currency,
    unsigned char * amount,
    unsigned char amount_size,
    char* printable_amount,
    unsigned char printable_amount_size);

#endif // _GET_PRINTABLE_AMOUN_H_