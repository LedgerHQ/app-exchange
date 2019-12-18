#ifndef _CHECK_ADDRESS_H_
#define _CHECK_ADDRESS_H_

int check_address(
    unsigned char* coin_config,
    unsigned char coin_config_length,
    unsigned char* address_parameters,
    unsigned char address_parameters_length,
    char * currency,
    char * address_to_check,
    char * address_extra_to_check);

#endif // _CHECK_ADDRESS_H_