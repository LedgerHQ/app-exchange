#ifndef _CHECK_ADDRESS_H_
#define _CHECK_ADDRESS_H_

int check_address(
    unsigned char* coin_config,
    unsigned char coin_config_length,
    unsigned char* address_parameters,
    unsigned char address_parameters_length,
    char * currency,
    unsigned char currency_length,
    char * address_to_check,
    unsigned char address_length,
    char * address_extra_to_check,
    unsigned char address_extra_length);

#endif // _CHECK_ADDRESS_H_