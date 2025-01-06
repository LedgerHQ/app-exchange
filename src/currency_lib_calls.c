#include <string.h>

#include "os_io_seproxyhal.h"
#include "cx.h"
#include "os.h"
#include "globals.h"
#include "swap_errors.h"

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

// BSS start and end defines symbols
extern void *_bss;
extern void *_ebss;
// Known at LINK time, not COMPILE time
#define BSS_SIZE ((uintptr_t)&_ebss - (uintptr_t)&_bss)

// Call the os_lib_call with a checksum before and after the call to ensure the child application
// did not corrupt our memory
// Caller needs to ensure that the child application will not write it's output in BSS, otherwise
// this function will yield a false positive
static int os_lib_call_bss_safe(unsigned int libcall_params[5]) {
    PRINTF("Check BSS from %p to %p\n", &_bss, &_ebss);
    // Make crc of the BSS before the lib call
    volatile uint16_t bss_crc_before = cx_crc16(&_bss, ((uintptr_t) &_ebss) - ((uintptr_t) &_bss));
    // Safeguard the BSS on the stack
    uint8_t *stack_ptr = __builtin_alloca(BSS_SIZE);
    memcpy(stack_ptr, &_bss, BSS_SIZE);

    // os_lib_call will throw SWO_SEC_APP_14 if the called application is not installed.
    // We DON'T define a local TRY / CATCH context because it costs a lot of stack and we are short
    // for some exchanged coins
    // This means we will fallback to the main function that will handle the error (error RAPDU)
    // TODO: once LNS is deprecated, handle the error properly here
    os_lib_call(libcall_params);

    // Copy back the safe copy of the BSS from the stack to its original place
    memcpy(&_bss, stack_ptr, BSS_SIZE);
    // Ensure the BSS is back to a valid state. Corruption can happen on our stack if the lib apps
    // Writes on it
    volatile uint16_t bss_crc_after = cx_crc16(&_bss, ((uintptr_t) &_ebss) - ((uintptr_t) &_bss));
    if (bss_crc_before != bss_crc_after) {
        PRINTF("BSS corrupted by the child application, %d != %d\n", bss_crc_before, bss_crc_after);
        return -1;
    }
    return 0;
}

uint16_t get_printable_amount(buf_t *coin_config,
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

    // Initialize result with error value.
    // This might be used in case the called app catch a throw and call os_lib_end()
    // before setting the result value.
    lib_in_out_params.printable_amount[0] = '\0';

    libcall_params[0] = (unsigned int) application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = GET_PRINTABLE_AMOUNT;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int) &lib_in_out_params;

    PRINTF("Exchange will call '%s' as library for GET_PRINTABLE_AMOUNT\n", application_name);
    if (os_lib_call_bss_safe(libcall_params) != 0) {
        return MEMORY_CORRUPTION;
    }
    PRINTF("Back in Exchange, the app finished the library command GET_PRINTABLE_AMOUNT\n");

    // the lib application should have something for us to display
    if (lib_in_out_params.printable_amount[0] == '\0') {
        PRINTF("Error: Printable amount should exist\n");
        return AMOUNT_FORMATTING_FAILED;
    }
    // result should be null terminated string, so we need to have at least one 0
    if (lib_in_out_params.printable_amount[sizeof(lib_in_out_params.printable_amount) - 1] !=
        '\0') {
        PRINTF("Error: Printable amount should be null-terminated\n");
        return AMOUNT_FORMATTING_FAILED;
    }
    if (strlcpy(printable_amount, lib_in_out_params.printable_amount, printable_amount_size) >=
        printable_amount_size) {
        PRINTF("strlcpy failed, destination too short for printable_amount\n");
    }
    PRINTF("Returned printable_amount '%s'\n", printable_amount);

    return 0;
}

uint16_t check_address(buf_t *coin_config,
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

    // Initialize result with error value.
    // This might be used in case the called app catch a throw and call os_lib_end()
    // before setting the result value.
    lib_in_out_params.result = 0;

    libcall_params[0] = (unsigned int) application_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = CHECK_ADDRESS;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int) &lib_in_out_params;

    PRINTF("Exchange will call '%s' as library for CHECK_ADDRESS\n", application_name);
    PRINTF("The address to check '%s'\n", lib_in_out_params.address_to_check);
    if (os_lib_call_bss_safe(libcall_params) != 0) {
        return MEMORY_CORRUPTION;
    }
    PRINTF("Back in Exchange, the app finished the library command CHECK_ADDRESS\n");
    PRINTF("Returned code %d\n", lib_in_out_params.result);

    if (lib_in_out_params.result != 1) {
        return INVALID_ADDRESS;
    }

    return 0;
}

int create_payin_transaction(create_transaction_parameters_t *lib_in_out_params,
                             bool *reported_result) {
    unsigned int libcall_params[5];

    libcall_params[0] = (unsigned int) G_swap_ctx->payin_binary_name;
    libcall_params[1] = 0x100;
    libcall_params[2] = SIGN_TRANSACTION;
    libcall_params[3] = 0;
    libcall_params[4] = (unsigned int) lib_in_out_params;

    PRINTF("Exchange will call '%s' as library for SIGN_TRANSACTION\n",
           G_swap_ctx->payin_binary_name);
    USB_power(0);

#ifdef HAVE_NBGL
    // Save appname in stack to keep it from being erased
    // We'll need it later for the failure modale on Stax
    // char appname[BOLOS_APPNAME_MAX_SIZE_B];
    // strlcpy(appname, G_swap_ctx->payin_binary_name, sizeof(appname));
#endif

    // Save G_swap_ctx and set it back after lib call
    swap_app_context_t *swap_ctx_addr = G_swap_ctx;

    // This os_lib_call may not throw SWO_SEC_APP_14 (missing library), as the existence of the
    // application has been enforced through an earlier call to os_lib_call for CHECK_ADDRESS and
    // GET_PRINTABLE_AMOUNT
    os_lib_call(libcall_params);

    G_swap_ctx = swap_ctx_addr;

    // From now on our BSS is corrupted and unusable. Return to main loop to start a new cycle ASAP
    PRINTF("Back in Exchange, the app finished the library command SIGN_TRANSACTION\n");
    PRINTF("Returned code %d\n", lib_in_out_params->result);

#ifdef HAVE_NBGL
    // Retrieve the appname from the stack and put it back in the BSS
    // strlcpy(G_previous_cycle_data.appname_last_cycle,
    //         appname,
    //         sizeof(G_previous_cycle_data.appname_last_cycle));
    // Remember if this sign was successful
    // G_previous_cycle_data.was_successful = (lib_in_out_params->result == 1);
#endif
    *reported_result = (lib_in_out_params->result == 1);

    return 0;
}
