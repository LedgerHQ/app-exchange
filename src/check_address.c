#include "check_address.h"
#include "os.h"
#include "swap_lib_calls.h"
#include "currency_application_map.h"

// return 1 if the addresses match, 0 otherwise
int check_address(
    unsigned char* coin_config,
    unsigned char coin_config_length,
    unsigned char* address_parameters,
    unsigned char address_parameters_length,
    char * currency,
    char * address_to_check,
    char * address_extra_to_check) {
    unsigned int libcall_params[3];
    get_address_in_parameters_t lib_input_params = {0};
    lib_input_params.coin_configuration = coin_config;
    lib_input_params.coin_configuration_length = coin_config_length;
    lib_input_params.address_parameters = address_parameters;
    lib_input_params.address_parameters_length = address_parameters_length;

    char * application_name = get_application_name(currency);
    if (application_name == 0) {
        PRINTF("Error: Unknown application for currency %s", currency);
        THROW(INVALID_PARAMETER);
    }
    libcall_params[0] = (unsigned int)application_name;
    libcall_params[1] = GET_ADDRESS_IN;
    libcall_params[2] = (unsigned int)&lib_input_params;
    PRINTF("I am before library call");
    os_lib_call(libcall_params);
    PRINTF("I am back from library with address");
    if (libcall_params[1] != GET_ADDRESS_OUT) {
        PRINTF("Error: Safety check failed on return from library");
        THROW(EXCEPTION_SECURITY);
    }
    if (lib_input_params.resulted_address[sizeof(lib_input_params.resulted_address) - 1] != 0) {
        PRINTF("Error: Returned address is invalid or too long");
        THROW(INVALID_PARAMETER);
    }
    if (lib_input_params.resulted_extra_id[sizeof(lib_input_params.resulted_extra_id) - 1] != 0) {
        PRINTF("Error: Returned address extra is invalid or too long");
        THROW(INVALID_PARAMETER);
    }
    if (strcmp(address_to_check, lib_input_params.resulted_address) != 0) {
        return 0;
    }
    if (strcmp(address_extra_to_check, lib_input_params.resulted_extra_id) != 0) {
        return 0;
    }
    return 1;
}