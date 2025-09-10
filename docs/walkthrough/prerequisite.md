Before proceeding with the SWAP integration, ensure that your application:

- Uses the [Standard Makefile](https://github.com/LedgerHQ/ledger-secure-sdk/blob/master/Makefile.standard_app).
- Follows the [Standard application format](https://github.com/LedgerHQ/ledger-secure-sdk/tree/master/lib_standard_app).
- Has the correct [tests structure](https://github.com/LedgerHQ/app-boilerplate/blob/master/tests/).

Although these steps may seem unrelated to the SWAP feature, it significantly simplifies the integration process to the point that no support is provided if you do without.

You should use the [app-boilerplate](https://github.com/LedgerHQ/app-boilerplate) as example and depending on the date of fork from the Boilerplate application, most of this steps can already be done.

## Standard Makefile

Ensure that, like the [Boilerplate Makefile](https://github.com/LedgerHQ/app-boilerplate/blob/master/Makefile), your Makefile contains:
```Makefile
include $(BOLOS_SDK)/Makefile.standard_app
```

## Standard application files

Ensure that, like the [Boilerplate Makefile](https://github.com/LedgerHQ/app-boilerplate/blob/master/Makefile), the `DISABLE_STANDARD_APP_FILES` is **not** set to `1`:

## Test structure

Ensure that your tests directory sticks to the following structure:
```sh
$> ls app-boilerplate/tests/
application_client
README.md
standalone
swap
```

--8<-- "docs/deps/app-boilerplate/tests/README.md"
