## Add the CAL data for your application

Please find more information about what the CAL is and how it is used in the [Crypto Asset List](../technical_informations/cal.md) section.

Add the coin configuration for your currency in the [test/python/apps/cal.py](https://github.com/LedgerHQ/app-exchange/blob/develop/test/python/apps/cal.py) file.

Do not use the subconfiguration field for now, you can add it later if you happen to need it, in the meantime the standard configuration will do fine for getting started. 

## Enable the Exchange tests for your application

Exchange tests are written in a factorized way. The core of the tests is done in the [ExchangeTestRunner](https://github.com/LedgerHQ/app-exchange/blob/develop/test/python/apps/exchange_test_runner.py) class.

Individual tests import and extend the ExchangeTestRunner class to leverage the test framework written inside. 

Write a first draft of the Exchange test for you application, you can take the TON test as an example.

[test/python/test_ton.py](https://github.com/LedgerHQ/app-exchange/blob/develop/test/python/test_ton.py)

The test consists of two parts:

- a `TonTests` class that extends `ExchangeTestRunner`.
- a `TestsTon` class that encompasses all `test_ton_*` tests that are expanded by its parametrization.

```Python
--8<-- "test/python/test_ton.py:native_test"
```

Create a `test_<appname>.py` that follows the same structure. You can leave the function `perform_final_tx()` empty for now if you want.

You can validate this step by running the `swap_ui_only()` test for your coin, it should pass as we coded empty yesmen shells for our tests.
