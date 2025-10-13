## Add the CAL data for your application

You can find more information about what the CAL is and how it is used in the [Crypto Asset List](../technical_information/cal.md) section.

Modify the [cal_helper.py](https://github.com/LedgerHQ/app-boilerplate/blob/master/tests/swap/cal_helper.py) file to craft your coin configuration instead of the Boilerplate one.

Do not use the `sub_coin_config` field for now. You can use it later for tokens if needed; for the time being, the standard configuration is sufficient to get started.

## Enable the Exchange tests for your application

The core of the Exchange tests is handled by the [ExchangeTestRunner](https://github.com/LedgerHQ/app-exchange/blob/develop/client/src/ledger_app_clients/exchange/test_runner.py) class in the Exchange test client.

Individual tests import and extend the ExchangeTestRunner class to leverage the test framework it provides.

Write a first draft of the Exchange tests for your application, using the Boilerplate tests as an example:

[tests/swap/test_boilerplate.py](https://github.com/LedgerHQ/app-boilerplate/blob/master/tests/swap/test_boilerplate.py)

You can leave the `perform_final_tx()` function empty for now if you prefer.

You can validate this step by running the `swap_ui_only()` test for your coin. It should pass, as we coded empty “yes-man” handlers for our tests in the previous section.
