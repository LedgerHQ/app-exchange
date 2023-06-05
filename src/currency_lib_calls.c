#include <string.h>

#include "os_io_seproxyhal.h"
#include "os.h"
#include "globals.h"

#include "currency_lib_calls.h"

/*
  Inter-application doc:

  `os_lib_call` is called with an `unsigned int [5]` argument.
  The first `int` is used to choose the app to start, the rest is used as
  this app's main arguments.
  For instance, in Ethereum 1.9.19, the final `int`s are casted into a struct
  like:

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

int get_printable_amount(buf_t *coin_config,
                         char *application_name,
                         unsigned char *amount,
                         unsigned char amount_size,
                         char *printable_amount,
                         unsigned char printable_amount_size,
                         bool is_fee) {
    unsigned int libcall_params[5];
    get_printable_amount_parameters_t lib_in_out_params;
    memset(&lib_in_out_params, 0, sizeof(lib_in_out_params));

    lib_in_out_params.coin_configuration = coin_config->bytes;
    lib_in_out_params.coin_configuration_length = coin_config->size;
    lib_in_out_params.amount = amount;
    lib_in_out_params.amount_length = amount_size;
    lib_in_out_params.is_fee = is_fee;

    libcall_params[0] = (unsigned int) application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = GET_PRINTABLE_AMOUNT;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int) &lib_in_out_params;

    PRINTF("Exchange will call '%s' as library for GET_PRINTABLE_AMOUNT\n", application_name);
    os_lib_call(libcall_params);
    PRINTF("Back in Exchange, the app finished the library command GET_PRINTABLE_AMOUNT\n");

    // the lib application should have something for us to display
    if (lib_in_out_params.printable_amount[0] == '\0') {
        PRINTF("Error: Printable amount should exist\n");
        return -1;
    }
    // result should be null terminated string, so we need to have at least one 0
    if (lib_in_out_params.printable_amount[sizeof(lib_in_out_params.printable_amount) - 1] !=
        '\0') {
        PRINTF("Error: Printable amount should be null-terminated\n");
        return -1;
    }
    strlcpy(printable_amount, lib_in_out_params.printable_amount, printable_amount_size);
    PRINTF("Returned printable_amount '%s'\n", printable_amount);

    return 0;
}

int check_address(buf_t *coin_config,
                  buf_t *address_parameters,
                  char *application_name,
                  char *address_to_check,
                  char *address_extra_to_check) {
    unsigned int libcall_params[5];
    check_address_parameters_t lib_in_out_params;
    memset(&lib_in_out_params, 0, sizeof(lib_in_out_params));

    lib_in_out_params.coin_configuration = coin_config->bytes;
    lib_in_out_params.coin_configuration_length = coin_config->size;
    lib_in_out_params.address_parameters = address_parameters->bytes;
    lib_in_out_params.address_parameters_length = address_parameters->size;
    lib_in_out_params.address_to_check = address_to_check;
    lib_in_out_params.extra_id_to_check = address_extra_to_check;

    libcall_params[0] = (unsigned int) application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = CHECK_ADDRESS;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int) &lib_in_out_params;

    PRINTF("Exchange will call '%s' as library for CHECK_ADDRESS\n", application_name);
    PRINTF("The address to check '%s'\n", lib_in_out_params.address_to_check);
    os_lib_call(libcall_params);
    PRINTF("Back in Exchange, the app finished the library command CHECK_ADDRESS\n");
    PRINTF("Returned code %d\n", lib_in_out_params.result);

    return lib_in_out_params.result;
}

int create_payin_transaction(create_transaction_parameters_t *lib_in_out_params) {
    unsigned int libcall_params[5];

    lib_in_out_params->result = 0;

    libcall_params[0] = (unsigned int) G_swap_ctx.payin_binary_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = SIGN_TRANSACTION;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int) lib_in_out_params;

    PRINTF("Exchange will call '%s' as library for SIGN_TRANSACTION\n", G_swap_ctx.payin_binary_name);
    USB_power(0);

#ifdef HAVE_NBGL
    // Save appname in stack to keep it from being erased
    // We'll need it later for the failure modale on Stax
    char appanme[BOLOS_APPNAME_MAX_SIZE_B];
    strlcpy(appanme, G_swap_ctx.payin_binary_name, sizeof(appanme));
#endif

    os_lib_call(libcall_params);

    // From now on our BSS is corrupted and unusable. Return to main loop to start a new cycle ASAP
    PRINTF("Back in Exchange, the app finished the library command SIGN_TRANSACTION\n");
    PRINTF("Returned code %d\n", lib_in_out_params->result);

#ifdef HAVE_NBGL
    // Retrieve the appname from the stack and put it back in the BSS
    strlcpy(G_swap_ctx.payin_binary_name, appanme, sizeof(G_swap_ctx.payin_binary_name));
#endif

    return lib_in_out_params->result;
}
