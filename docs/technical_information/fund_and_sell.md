The **SWAP** feature refers to trading an amount of a **FROM** crypto against an amount of a **TO** crypto.

The **FUND** feature refers to sending an amount of a **FROM** crypto to an external account (for example, funding a debit card).

The **SELL** feature refers to trading an amount of a **FROM** crypto against a **FIAT** amount.

From the perspective of the library application, the **FUND** and **SELL** specificities are irrelevant and have no difference with the **SWAP** feature.  
They only impact the APDUs exchanged between Ledger Wallet and the Exchange application.  

In the test framework, this behavior is entirely handled by the **ExchangeTestRunner**.
