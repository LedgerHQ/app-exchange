#include "check_address.h"
#include "os.h"
#include "swap_lib_calls.h"
#include "utils.h"

char *get_application_name(char* currency_name, unsigned char currency_name_length) {
    // TODO add proper application lookup table
    return "Bitcoin";
}

// return 1 if the addresses match, 0 otherwise
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
    unsigned char address_extra_length) {
    unsigned int libcall_params[3];
    get_address_in_parameters_t lib_input_params;
    lib_input_params.coin_configuration = coin_config;
    lib_input_params.coin_configuration_length = coin_config_length;
    lib_input_params.address_parameters = address_parameters;
    lib_input_params.address_parameters_length = address_parameters_length;

    libcall_params[0] = (unsigned int)get_application_name(currency, currency_length);
    libcall_params[1] = GET_ADDRESS_IN;
    libcall_params[2] = (unsigned int)&lib_input_params;
    PRINTF("I am before library call\n");
    os_lib_call(libcall_params);
    PRINTF("I am back from library with address\n");
    if (libcall_params[1] != GET_ADDRESS_OUT) {
        PRINTF("Error: Safety check failed on return from library\n");
        THROW(EXCEPTION_SECURITY);
    }
    if (strcmp_non_zero(address_to_check, address_length, lib_input_params.resulted_address, sizeof(lib_input_params.resulted_address)) != 0) {
        return 0;
    }
    if (strcmp_non_zero(address_extra_to_check, address_extra_length, lib_input_params.resulted_extra_id, sizeof(lib_input_params.resulted_extra_id)) != 0) {
        return 0;
    }
    return 1;
}