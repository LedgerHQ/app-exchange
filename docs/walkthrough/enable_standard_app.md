## Add the CAL data for your application

Please find more information about what the CAL is and how it is used in the [Crypto Asset List](../technical_informations/cal.md) section.

Modify the [cal_helper.py](https://github.com/LedgerHQ/app-boilerplate/blob/master/tests/swap/cal_helper.py) file to craft your coin configuration instead of the Boilerplate one.

Do not use the `sub_coin_config` field for now, you can use it later for tokens if you happen to need it, in the meantime the standard configuration will do fine for getting started.

## Enable the Exchange tests for your application

The core of the Exchange tests are handled by the [ExchangeTestRunner](https://github.com/LedgerHQ/app-exchange/blob/develop/client/src/ledger_app_clients/exchange/test_runner.py) class in the Exchange test client

Individual tests import and extend the ExchangeTestRunner class to leverage the test framework written inside.

Write a first draft of the Exchange tests for you application, taking the Boilerplate tests as an example.

[tests/swap/test_boilerplate.py](https://github.com/LedgerHQ/app-boilerplate/blob/master/tests/swap/test_boilerplate.py)

You can leave the function `perform_final_tx()` empty for now if you want.

You can validate this step by running the `swap_ui_only()` test for your coin, it should pass as we coded empty yesmen handles for our tests in the previous section.
