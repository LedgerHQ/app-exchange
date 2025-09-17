## Enable the SWAP feature

In the Makefile, set the variable `ENABLE_SWAP = 1` or `ENABLE_TESTING_SWAP = 1` of the standard Makefile, as shown in the example below:

[`app-boilerplate/Makefile`](https://github.com/LedgerHQ/app-boilerplate/blob/master/Makefile)
```Makefile
--8<-- "docs/deps/app-boilerplate/Makefile:variables"
```

Then compile your application, you **may** encounter the following error if you do not have a recent Boilerplate fork:

```sh
ld.lld: error: undefined symbol: swap_copy_transaction_parameters
>>> referenced by main.c
>>>               build/nanox/obj/sdk/lib_standard_app/main.o:(library_app_main)

ld.lld: error: undefined symbol: swap_handle_get_printable_amount
>>> referenced by main.c
>>>               build/nanox/obj/sdk/lib_standard_app/main.o:(library_app_main)

ld.lld: error: undefined symbol: swap_handle_check_address
>>> referenced by main.c
>>>               build/nanox/obj/sdk/lib_standard_app/main.o:(library_app_main)
``` 

These errors are caused by the missing handler definitions. For more information about what the handlers do, refer to the [handler documentation](../technical_information/coin_application_api/index.md).

## Fix compilation errors if any

*If the compilation succeeds, you can skip this section.*

For now, we will declare the handlers in the simplest possible way.

Add the following files to your application (it is recommended to follow the Boilerplate file structure):
```sh
$> ls app-boilerplate/src/swap/
handle_check_address.c  handle_get_printable_amount.c  handle_swap.h  handle_swap_sign_transaction.c
```

Add the function declarations in the `.h` files and the function definitions in the `.c` files. Define empty functions for now:

```C
#include "os.h"
#include "swap_lib_calls.h"

void swap_handle_check_address(check_address_parameters_t *params) {
    // Accept all addresses
    params->result = 1;
}

void swap_handle_get_printable_amount(get_printable_amount_parameters_t* params) {
    // Format all amounts as 10
    strcpy(params->printable_amount, "10");
}

bool swap_copy_transaction_parameters(create_transaction_parameters_t* params) {
    // Do nothing successfully
    return true;
}
```
