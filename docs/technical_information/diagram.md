# Sequence diagram of a SWAP

This diagram showcases:

- The APDU and RAPDU exchanged between the Ledger Wallet and the Exchange application during a SWAP.
- The `os_lib_calls` commands made by the Exchange application to the involved Coin applications. 


Please look at the [protocol documentation](./protocol.md) to know more about how the APDUs content.

```mermaid
sequenceDiagram
    participant LL as Ledger Wallet
    participant EA as Exchange App
    participant TOCA as TO Coin App
    participant FRCA as FROM Coin App
    participant DS as Device Screen

    LL->>EA: START_NEW_TRANSACTION<br/>(0x03)
    activate EA
    EA-->>EA: Create a nonce for the transaction
    EA-->>LL: Device Transaction ID (nonce)

    LL->>EA: SET_PARTNER_KEY<br/>(0x04)
    EA-->>EA: Set the credentials of the exchange partner
    EA-->>LL: return

    LL->>EA: CHECK_PARTNER<br/>(0x05)
    EA-->>EA: Check that the credentials of the exchange<br/>partner are signed by the Ledger key
    EA-->>LL: return

    LL->>EA: PROCESS_TRANSACTION_RESPONSE<br/>(0x06)
    EA-->>EA: Receive and parse the transaction<br/>proposal from the exchange partner
    EA-->>LL: return

    LL->>EA: CHECK_TRANSACTION_SIGNATURE<br/>(0x07)
    EA-->>EA: Check that the transaction proposal<br/>is signed by the exchange partner
    EA-->>LL: return

    LL->>EA: CHECK_PAYOUT_ADDRESS<br/>(0x08)
    EA-->>TOCA: CHECK_ADDRESS os_lib_call()
    activate TOCA
    TOCA-->>TOCA: Check that the [payout] address is owned by the device
    TOCA-->>EA: os_lib_end(): Result
    deactivate TOCA
    EA->>TOCA: GET_PRINTABLE_AMOUNT os_lib_call()
    activate TOCA
    TOCA-->>TOCA: Format the receiving amount
    TOCA-->>EA: os_lib_end(): Formatted amount
    deactivate TOCA
    EA-->>LL: return

    LL->>EA: CHECK_REFUND_ADDRESS_NO_DISPLAY<br/>(0x0C)
    EA->>FRCA: CHECK_ADDRESS os_lib_call()
    activate FRCA
    FRCA-->>FRCA: Check that the [refund] address belongs to the device
    FRCA-->>EA: os_lib_end(): Result
    deactivate FRCA
    EA->>FRCA: GET_PRINTABLE_AMOUNT os_lib_call()
    activate FRCA
    FRCA-->>FRCA: Format the sending amount
    FRCA-->>EA: os_lib_end(): Formatted amount
    deactivate FRCA
    EA->>FRCA: GET_PRINTABLE_AMOUNT os_lib_call()
    activate FRCA
    FRCA-->>FRCA: Format the fees amount
    FRCA-->>EA: os_lib_end(): Formatted amount
    deactivate FRCA
    EA-->>LL: return

    LL->>EA: PROMPT_UI_DISPLAY<br/>(0x0F)
    EA->>DS: Request UI validation
    activate DS
    DS-->>DS: Display all the transaction data<br/>ask user to confirm
    DS-->>EA: User confirmation
    deactivate DS
    EA-->>LL: return

    LL->>EA: START_SIGNING_TRANSACTION<br/>(0x0A)
    EA-->>LL: Ok
    EA->>FRCA: SIGN_TRANSACTION os_lib_call()
    activate FRCA
    deactivate EA
    FRCA-->>FRCA: Save data validated by the user
    LL->>FRCA: Sign transaction request
    FRCA-->>FRCA: Check that the data to sign is the same<br/>as the data validated by the user + Sign
    FRCA-->>LL: Signed transaction
    FRCA-->>EA: os_lib_end()
    deactivate FRCA
    activate EA
    EA-->>EA: Save last cycle data:<br/>Coin appname + sign status
    EA-->>EA: Check if previous cycle
    EA-->>DS: if previous cycle
    activate DS
    DS-->>DS: display sign status
    DS-->>EA: 
    deactivate DS
    deactivate EA
```

The FUND and SELL flows are not described as they are only subsets of the SWAP flow.
