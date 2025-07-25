The Crypto Asset List is there to tackle two issues:

- The Exchange application does not know which application to call to handle a given currency.
- The Coin application may not have all data on hand to handle a given currency.

We solve these issues by using the CAL to give trusted information to the Exchange application.

### The CAL signature

The data of the CAL is stored on a HSM alongside its signature.

The signature is checked by the Exchange application upon reception of CAL data to ensure that the data is legitimate.

In order to be able to test with dynamic data, the Exchange application can be compiled with the `TEST_PUBLIC_KEY=1` flag to accept a false Ledger HSM key.
The resulting application will not work in production but is useful in our test framework.

### The coin configuration format

A coin configuration of a currency contains the following elements:

--8<-- "docs/technical_informations/protocol.md:coin_configuration"

### The subconfiguration

The `subconfiguration` part is optional and is often used only when handling tokens.

It's content is application specific, the bytes array will be given as pointer to the handles in the coin application,
for more information about the handles please refer to the corresponding section [Coin Application API](coin_application_api/index.md)

A standard subconfiguration exists, it is composed of `ticker + decimals`, it is the one used by most of our applications when handling tokens (Ethereum and Solana for example).

### How to craft a coin configuration

The **Ragger** tool provides utilities to craft coin configurations both without and with standard subconfiguration.

The **Exchange client** provides helper classes to insert the coin configuration in our tests.

[client/src/ledger_app_clients/exchange/cal_helper.py](https://github.com/LedgerHQ/app-exchange/blob/develop/client/src/ledger_app_clients/exchange/cal_helper.py)
```Python
--8<-- "client/src/ledger_app_clients/exchange/cal_helper.py"
```

As an example, here is the craft of the coin configuration for the Boilerplate example application in our tests:

[tests/swap/cal_helper.py](https://github.com/LedgerHQ/app-boilerplate/blob/master/tests/swap/cal_helper.py)
```Python
--8<-- "docs/deps/app-boilerplate/tests/swap/cal_helper.py"
```
