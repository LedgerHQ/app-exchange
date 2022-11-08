#include <string.h>

#include "os.h"
#include "os_io_seproxyhal.h"

#include "currency_lib_calls.h"

/*
  Inter-application doc:

  `os_lib_call` is called with an `unsigned int [5]` argument.
  The first argument is used to choose the app to start, the rest is used as
  this app's main arguments.
  For instance, in Ethereum 1.9.19, the args are casted into a struct like:

  ```
  struct libargs_s {
    unsigned int id;
    unsigned int command;
    chain_config_t *chain_config;
    union {
      check_address_parameters_t *check_address;
      create_transaction_parameters_t *create_transaction;
      get_printable_amount_parameters_t *get_printable_amount;
    };
  };
  ```
  ... so, in the following functions, the mapping is:

  `libcall_params[1]` -> `libargs_s.id`
  `libcall_params[2]` -> `libargs_s.command`
  `libcall_params[3]` -> `libargs_s.chain_config`
  `libcall_params[4]` -> `libargs_s` union
 */

int get_printable_amount(const buf_t* const coin_config,
    const char* const application_name,
    const unsigned char* const amount,
    const unsigned char amount_size,
    char* const printable_amount,
    const unsigned char printable_amount_size,
    const bool is_fee)
{
    static unsigned int libcall_params[5];
    static get_printable_amount_parameters_t lib_input_params = { 0 };
    lib_input_params.coin_configuration = coin_config->bytes;
    lib_input_params.coin_configuration_length = coin_config->size;
    lib_input_params.amount = amount;
    lib_input_params.amount_length = amount_size;
    lib_input_params.is_fee = is_fee;
    libcall_params[0] = (unsigned int)application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = GET_PRINTABLE_AMOUNT;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int)&lib_input_params;
    PRINTF("Address of printable_amount %d\n", lib_input_params.printable_amount);
    memset(lib_input_params.printable_amount, 0, sizeof(lib_input_params.printable_amount));
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
    strncpy(printable_amount, lib_input_params.printable_amount, printable_amount_size);
    printable_amount[printable_amount_size - 1] = '\x00';
    return 0;
}

int check_address(buf_t* coin_config,
    buf_t* address_parameters,
    char* application_name,
    char* address_to_check,
    char* address_extra_to_check)
{
    static unsigned int libcall_params[5];
    static check_address_parameters_t lib_in_out_params = { 0 };
    lib_in_out_params.coin_configuration = coin_config->bytes;
    lib_in_out_params.coin_configuration_length = coin_config->size;
    lib_in_out_params.address_parameters = address_parameters->bytes;
    lib_in_out_params.address_parameters_length = address_parameters->size;
    lib_in_out_params.address_to_check = address_to_check;
    lib_in_out_params.extra_id_to_check = address_extra_to_check;
    libcall_params[0] = (unsigned int)application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = CHECK_ADDRESS;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int)&lib_in_out_params;
    PRINTF("I am calling %s to check address\n", application_name);
    PRINTF("I am going to check address %s\n", lib_in_out_params.address_to_check);
    // Speculos workaround
    // io_seproxyhal_general_status();
    os_lib_call(libcall_params);
    // PRINTF("Debug data sent by library %.*H\n", 20, lib_in_out_params.address_to_check);
    PRINTF("I am back\n");
    return lib_in_out_params.result;
}

void create_payin_transaction(char* application_name,
    create_transaction_parameters_t* lib_in_out_params)
{
    unsigned int libcall_params[5];
    libcall_params[0] = (unsigned int)application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = SIGN_TRANSACTION;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int)lib_in_out_params;
    PRINTF("Calling %s app\n", application_name);
    USB_power(0);
    os_lib_call(libcall_params);
    USB_power(0);
    USB_power(1);
}
