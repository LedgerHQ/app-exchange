The Crypto Asset List is designed to address two issues:

- The Exchange application does not know which application to call to handle a given currency.
- The Coin application may not have all the data required to handle a given currency.

These issues are solved by using the CAL to provide trusted information to the Exchange application.

### The CAL signature

The CAL data is stored on an HSM alongside its signature.

The signature is checked by the Exchange application upon reception of CAL data to ensure that the data is legitimate.

To allow testing with dynamic data, the Exchange application can be compiled with the `TEST_PUBLIC_KEY=1` flag to accept a false Ledger HSM key.  
The resulting application will not work in production but is useful in the test framework.

### The coin configuration format

A coin configuration for a currency contains the following elements:

--8<-- "docs/technical_information/protocol.md:coin_configuration"

### The subconfiguration

The `subconfiguration` part is optional and is often used only when handling tokens.

Its content is application-specific. The byte array will be passed as a pointer to the handlers in the coin application.  
For more information about the handlers, please refer to the corresponding section: [Coin Application API](coin_application_api/index.md).

A standard subconfiguration exists, composed of `ticker + decimals`. This is the one used by most of our applications when handling tokens (for example, Ethereum and Solana).

The **Ragger** tool provides utilities to craft coin configurations both without and with the standard subconfiguration.

As an example, here is the crafting of the coin configuration for Solana in our tests:

[app-solana/tests/application_client/solana_utils.py](https://github.com/LedgerHQ/app-solana/blob/develop/tests/application_client/solana_utils.py)
```Python
--8<-- "docs/deps/app-solana/tests/application_client/solana_utils.py:solana_coin_conf_includes"

--8<-- "docs/deps/app-solana/tests/application_client/solana_utils.py:solana_coin_conf"
```

[tests/swap/cal_helper.py](https://github.com/LedgerHQ/app-solana/blob/develop/tests/swap/cal_helper.py)
```Python
--8<-- "docs/deps/app-solana/tests/swap/cal_helper.py:sol_conf"
```
