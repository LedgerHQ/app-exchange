This page provides all the essential setup details to help you get started on enabling the **SWAP** feature in your application.

The [Boilerplate application](https://github.com/LedgerHQ/app-boilerplate) will be used as example.

## Understanding the Exchange test framework

Please look at the [sequence diagram](../technical_informations/diagram.md). You will see that in order to perform a **SWAP**, several communication and authentication steps between the Ledger Live (here mocked by Ragger) and the device are needed.

These steps are out of the scope of testing your application, and we provide the [Exchange client](https://pypi.org/project/ledger-app-clients.exchange/) hosted in the [Exchange application repository](https://github.com/LedgerHQ/app-exchange/tree/develop/client) to perform it automatically.

Looking at the [sequence diagram](../technical_informations/diagram.md), the only python code you will have to write is the **Sign transaction request** once your application has been started by Exchange.

--8<-- "docs/deps/app-boilerplate/tests/swap/README.md"

---

## Next steps

Now you know how to setup and run the swap tests, you'll be able to add the tests for your own application and run them as you develop the SWAP feature in your application.
