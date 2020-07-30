#include "currency_lib_calls.h"
#include "ux.h"

int get_printable_amount(unsigned char *coin_config, unsigned char coin_config_length,  //
                         char *application_name,                                        //
                         unsigned char *amount, unsigned char amount_size,              //
                         char *printable_amount, unsigned char printable_amount_size,   //
                         bool is_fee) {
    static unsigned int libcall_params[5];
    static get_printable_amount_parameters_t lib_input_params = {0};
    lib_input_params.coin_configuration = coin_config;
    lib_input_params.coin_configuration_length = coin_config_length;
    lib_input_params.amount = amount;
    lib_input_params.amount_length = amount_size;
    lib_input_params.is_fee = is_fee;
    libcall_params[0] = (unsigned int) application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = GET_PRINTABLE_AMOUNT;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int) &lib_input_params;
    PRINTF("Address of printable_amount %d\n", lib_input_params.printable_amount);
    os_memset(lib_input_params.printable_amount, 0, sizeof(lib_input_params.printable_amount));
    // Speculos workaround
    // io_seproxyhal_general_status();
    os_lib_call(libcall_params);
    // result should be null terminated string, so we need to have at least one 0
    if (lib_input_params.printable_amount[sizeof(lib_input_params.printable_amount) - 1] != 0) {
        PRINTF("Error: Printable amount should be null-terminated\n");
        return -1;
    }
    if (strlen(lib_input_params.printable_amount) >= printable_amount_size) {
        PRINTF("Error: Printable amount is too big to fit into input buffer\n");
        return -1;
    }
    strcpy(printable_amount, lib_input_params.printable_amount);
    return 0;
}

int check_address(unsigned char *coin_config, unsigned char coin_config_length,                //
                  unsigned char *address_parameters, unsigned char address_parameters_length,  //
                  char *application_name,                                                      //
                  char *address_to_check,                                                      //
                  char *address_extra_to_check) {
    static unsigned int libcall_params[5];
    static check_address_parameters_t lib_in_out_params = {0};
    lib_in_out_params.coin_configuration = coin_config;
    lib_in_out_params.coin_configuration_length = coin_config_length;
    lib_in_out_params.address_parameters = address_parameters;
    lib_in_out_params.address_parameters_length = address_parameters_length;
    lib_in_out_params.address_to_check = address_to_check;
    lib_in_out_params.extra_id_to_check = address_extra_to_check;
    libcall_params[0] = (unsigned int) application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = CHECK_ADDRESS;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int) &lib_in_out_params;
    PRINTF("I am calling %s to check address\n", application_name);
    PRINTF("I am going to check address %s\n", lib_in_out_params.address_to_check);
    // Speculos workaround
    // io_seproxyhal_general_status();
    os_lib_call(libcall_params);
    PRINTF("I am back\n");
    return lib_in_out_params.result;
}

void create_payin_transaction(char *application_name,
                              create_transaction_parameters_t *lib_in_out_params) {
    unsigned int libcall_params[5];
    libcall_params[0] = (unsigned int) application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = SIGN_TRANSACTION;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int) lib_in_out_params;
    PRINTF("Calling %s app\n", application_name);
    USB_power(0);
    os_lib_call(libcall_params);
    USB_power(0);
    USB_power(1);
}
