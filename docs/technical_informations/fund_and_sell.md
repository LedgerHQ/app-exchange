The **SWAP** feature refers to trading an amount of a **FROM** crypto against an amount of a **TO** crypto.

The **FUND** feature refers to sending an amount of a **FROM** crypto to an external account (funding a debit card for example)

The **SELL** feature refers to trading an amount of a **FROM** crypto against a FIAT amount.

The **FUND** and **SELL** specificities are irrelevant from the library application and have no difference with the **SWAP** feature in that regard. It only impacts the APDUs exchanged between the Ledger Live and the Exchange application. In the test framework, it is entirely handled by the ExchangeTestRunner. 
