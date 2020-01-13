#include "currency_lib_calls.h"
#include "swap_lib_calls.h"

int get_printable_amount(
    unsigned char* coin_config,
    unsigned char coin_config_length,
    char * application_name,
    unsigned char * amount,
    unsigned char amount_size,
    char* printable_amount,
    unsigned char printable_amount_size) {
    unsigned int libcall_params[3];
    get_printable_amount_parameters_t lib_input_params = {0};
    lib_input_params.coin_configuration = coin_config;
    lib_input_params.coin_configuration_length = coin_config_length;
    lib_input_params.amount = amount;
    lib_input_params.amount_length = amount_size;
    libcall_params[0] = (unsigned int)application_name;
    libcall_params[1] = GET_PRINTABLE_AMOUNT_IN;
    libcall_params[2] = (unsigned int)&lib_input_params;
    os_lib_call(libcall_params);
    if (libcall_params[1] != GET_PRINTABLE_AMOUNT_OUT) {
        PRINTF("Error: Safety check failed on return from library");
        return -1;
    }
    // result should be null terminated string, so we need to have at least one 0
    if (lib_input_params.printable_amont[printable_amount_size - 1] != 0) {
        PRINTF("Error: Printable amount should be null-terminated");
        return -1;
    }
    if (strlen(lib_input_params.printable_amont) >= printable_amount_size) {
        PRINTF("Error: Printable amount is too big to fit into input buffer");
        return -1;
    }
    strcpy(printable_amount, strlen(lib_input_params.printable_amont));
    return 0;
}

int check_address(
    unsigned char* coin_config,
    unsigned char coin_config_length,
    unsigned char* address_parameters,
    unsigned char address_parameters_length,
    char * application_name,
    char * address_to_check,
    char * address_extra_to_check) {
    unsigned int libcall_params[3];
    check_address_parameters_t lib_in_out_params = {0};
    lib_in_out_params.coin_configuration = coin_config;
    lib_in_out_params.coin_configuration_length = coin_config_length;
    lib_in_out_params.address_parameters = address_parameters;
    lib_in_out_params.address_parameters_length = address_parameters_length;
    libcall_params[0] = (unsigned int)application_name;
    libcall_params[1] = CHECK_ADDRESS_IN;
    libcall_params[2] = (unsigned int)&lib_in_out_params;
    os_lib_call(libcall_params);
    if (libcall_params[1] != CHECK_ADDRESS_OUT) {
        PRINTF("Error: Safety check failed on return from library");
        return -1;
    }
    return lib_in_out_params.result;
}

void create_payin_transaction(
    unsigned char* coin_config,
    unsigned char coin_config_length,
    char * application_name,
    unsigned char * amount,
    unsigned char amount_size,
    char * payin_address,
    char * payin_address_extra_id) {
    create_transaction_parameters_t lib_in_out_params = {0};
    lib_in_out_params.amount = amount;
    lib_in_out_params.amount_length = amount_size;
    lib_in_out_params.coin_configuration = coin_config;
    lib_in_out_params.coin_configuration_length = coin_config_length;
    lib_in_out_params.destination_address = payin_address;
    lib_in_out_params.destination_address_extra_id = payin_address_extra_id;
    unsigned int libcall_params[3];
    libcall_params[0] = (unsigned int)application_name;
    libcall_params[1] = CHECK_ADDRESS_IN;
    libcall_params[2] = (unsigned int)&lib_in_out_params;
    os_lib_call(libcall_params);
    if (libcall_params[1] != CHECK_ADDRESS_OUT) // doesn't affect application flow, just for logging
        PRINTF("Error: Safety check failed on return from library");
}
