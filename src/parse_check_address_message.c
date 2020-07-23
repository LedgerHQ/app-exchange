#include "parse_check_address_message.h"
#include "globals.h"
//                                                      offset
// 1 byte (length X of "to" currency configuration)     0
// X bytes ("to" currency configuration)                1
// D bytes = 2 + C (DER serialized signature):          1 + X
//    1 byte 0x30                                       1 + X
//    1 byte length C of compoind object                2 + X
//    C bytes
// 1 byte length Y of address paramaters                1 + X + D
// Y bytes of address parameters                        2 + X + D
int parse_check_address_message(unsigned char *input_buffer, unsigned char input_buffer_length,  //
                                unsigned char **config, unsigned char *config_length,            //
                                unsigned char **der, unsigned char *der_length,                  //
                                unsigned char **address_parameters,
                                unsigned char *address_parameters_length) {
    if (input_buffer_length < MIN_DER_SIGNATURE_LENGTH + 2) {
        return 0;
    }

    *config_length = input_buffer[0];
    *config = input_buffer + 1;

    if (input_buffer_length < 2 + MIN_DER_SIGNATURE_LENGTH + *config_length) {
        return 0;
    }

    *der_length = input_buffer[1 + *config_length + 1] + 2;
    *der = input_buffer + 1 + *config_length;

    if (*der_length < MIN_DER_SIGNATURE_LENGTH ||  //
        *der_length > MAX_DER_SIGNATURE_LENGTH ||  //
        input_buffer_length < 2 + *der_length + *config_length) {
        return 0;
    }

    *address_parameters_length = input_buffer[1 + *config_length + *der_length];
    *address_parameters = input_buffer + 1 + *config_length + *der_length + 1;

    if (input_buffer_length != 1 + *config_length + *der_length + 1 + *address_parameters_length) {
        return 0;
    }

    return 1;
}
