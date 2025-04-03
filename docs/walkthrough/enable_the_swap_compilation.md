## Enable the SWAP feature

In the Makefile, set the variable `ENABLE_SWAP = 1` of the standard Makefile as in the example below.

[`app-solana/Makefile`](https://github.com/LedgerHQ/app-solana/blob/develop/Makefile)
```Make
--8<-- "docs/deps/app-solana/Makefile:variables"
```

Then compile your application, you should encounter the following error:

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

They are caused by the missing handles definition. To know more about what the handles do, you can refer to the [handle documentation](../technical_informations/coin_application_api/index.md).

## Fix compilation errors

For now we will declare the handles in the most basic possible way.

Add the following files to your application, it is recommended to follow the following file structure:

```sh
$> ls ../app-solana/src/swap/
handle_check_address.c  handle_get_printable_amount.c  handle_swap_sign_transaction.c
handle_check_address.h  handle_get_printable_amount.h  handle_swap_sign_transaction.h
```

Add the functions declarations in the `.h` files and the functions definitions in the `.c` files. Define empty functions for now.
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

## Copy your compiled binary

Copy the binary compiled above into the Exchange library directory `app-exchange/test/python/lib_binaries/` under the name `<VARIANT_VALUES>_device.elf`, with `VARIANT_VALUES` from your Makefile.

Add your application to the [test/python/conftest.py](https://github.com/LedgerHQ/app-exchange/blob/develop/test/python/conftest.py) file.

```Python
--8<-- "test/python/conftest.py:sideloaded_applications"
```

You can run an unrelated Exchange test as done in the [Run a simple test](run_first_test.md) section to validate the sideloading of your application. 
