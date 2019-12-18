#include "get_printable_amount.h"
#include "swap_lib_calls.h"
#include "os.h"
#include "errors.h"
#include "currency_application_map.h"

int get_printable_amount(
    unsigned char* coin_config,
    unsigned char coin_config_length,
    char * currency,
    unsigned char * amount,
    unsigned char amount_size,
    char* printable_amount,
    unsigned char printable_amount_size) {
    unsigned int libcall_params[3];
    get_printable_amount_in_parameters_t lib_input_params = {0};
    lib_input_params.coin_configuration = coin_config;
    lib_input_params.coin_configuration_length = coin_config_length;
    lib_input_params.amount = amount;
    lib_input_params.amount_length = amount_size;
    char * application_name = get_application_name(currency);
    if (application_name == 0) {
        PRINTF("Error: Unknown application for currency %s", currency);
        THROW(INVALID_PARAMETER);
    }
    libcall_params[0] = (unsigned int)application_name;
    libcall_params[1] = GET_PRINTABLE_AMOUNT_IN;
    libcall_params[2] = (unsigned int)&lib_input_params;
    PRINTF("I am before library call");
    os_lib_call(libcall_params);
    PRINTF("I am back from library with address");
    if (libcall_params[1] != GET_PRINTABLE_AMOUNT_OUT) {
        PRINTF("Error: Safety check failed on return from library");
        THROW(EXCEPTION_SECURITY);
    }
    // result should be null terminated string, so se need to have at least one 0
    if (lib_input_params.printable_amont[printable_amount_size - 1] != 0) {
        PRINTF("Error: Printable amount should be null-terminated");
        THROW(INVALID_PARAMETER);
    }
    if (strlen(lib_input_params.printable_amont) >= printable_amount_size) {
        PRINTF("Error: Printable amount is too big to fit into input buffer");
        THROW(INVALID_PARAMETER);
    }
    strcpy(printable_amount, strlen(lib_input_params.printable_amont));
    return 0;
}