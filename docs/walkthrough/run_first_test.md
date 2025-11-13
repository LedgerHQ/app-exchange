This page provides all the essential setup details to help you get started with enabling the **SWAP** feature in your application.

The [Boilerplate application](https://github.com/LedgerHQ/app-boilerplate) will be used as an example.

## Understanding the Exchange test framework

Please look at the [sequence diagram](../technical_information/diagram.md). You will see that, in order to perform a **SWAP**, several communication and authentication steps between Ledger Wallet (here mocked by Ragger) and the device are required.

These steps are outside the scope of testing your application. We provide the [Exchange client](https://pypi.org/project/ledger-app-clients.exchange/), hosted in the [Exchange application repository](https://github.com/LedgerHQ/app-exchange/tree/develop/client), to perform them automatically.

Looking again at the [sequence diagram](../technical_information/diagram.md), the only Python code you will have to write is the **Sign transaction request** once your application has been started by Exchange.

--8<-- "docs/deps/app-boilerplate/tests/swap/README.md"

---

## Next steps

Now that you know how to set up and run the swap tests, you will be able to add tests for your own application and run them as you develop the **SWAP** feature.
