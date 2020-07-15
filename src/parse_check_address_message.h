#ifndef _PARSE_CHECK_ADDRESS_MESSAGE_H_
#define _PARSE_CHECK_ADDRESS_MESSAGE_H_

int parse_check_address_message(unsigned char *input_buffer, unsigned char input_buffer_length,  //
                                unsigned char **config, unsigned char *config_length,            //
                                unsigned char **der, unsigned char *der_length,                  //
                                unsigned char **address_parameters,
                                unsigned char *address_parameters_length);

#endif