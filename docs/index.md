# Ledger Swap documentation

This documentation is designed to help you understand how the **Ledger Swap** feature works and to guide you through modifying your coin application to be compatible with it.

The **Swap** feature enables users to securely exchange one cryptocurrency for another directly from their Ledger device, within Ledger Live. It uses a trusted, multi-step process to facilitate communication between **Ledger Live**, the **Trade Partner**, the **Exchange application**, and the respective **Coin applications** on the device.

Built with robust security at every stage, the process includes cryptographic validation and transaction signatures. Final confirmation is conducted directly on the device screen, ensuring that only validated transactions are signed and authorized.

## Key Components of the Swap Flow

The Swap process involves the following actors:

- The **Trade Partner**: Proposes a trade offer to the Ledger Live user, which must be clearly displayed on the device screen by the Exchange application.
- The **Ledger Live**: initiates and manages the transaction flow between the Partner and the Exchange application.
- The **Exchange Application**: serves as the intermediary between the Ledger Live, the involved coin applications, and the user.
- The **Coin Applications**: Handle the processing for both the **FROM** and **TO** currencies involved in the swap.
- The **Ledger Crypto Asset List (CAL)**: Contains HSM-signed data of all SWAP-compatible currencies that help the Exchange application display the transaction proposal content on screen. 

```mermaid
---
title: Swap FROM currency -> TO currency actors
---
flowchart LR
    classDef invisible width:0px,height:0px,stroke-width:0px,fill:transparent;

    subgraph P[TRADE PARTNER]
        PAR@{ shape: rounded, label: "Trade partner" }
    end

    subgraph HSM[LEDGER HSM]
        CAL@{ shape: rounded, label: "Crypto<br>Asset List" }
    end

    subgraph LL[LEDGER LIVE]
        LLC@{ shape: rounded, label: "Ledger Live" }
        %% Fake node to force the Partner -> Exchange line to go through the LL box
        FAKE((" ")):::invisible
    end

    subgraph D[DEVICE]
        EX@{ shape: rounded, label: "Exchange<br>application" }
        FROM@{ shape: rounded, label: "FROM<br>Coin application" }
        TO@{ shape: rounded, label: "TO<br>Coin application" }
        SCREEN@{ shape: rounded, label: "Device screen" }
    end

    PAR <-- "<div style='background:transparent;'>Trade<br>establishment" -->LLC
    PAR -- "<div style='background:transparent;'>Signed transaction<br>proposal" ---FAKE

    CAL -- "<div style='background:transparent;'>Coin<br>configurations" --- FAKE

    LLC <-- "<div style='background:transparent;'>Final payment request<br>/<br>Signature or refusal" -->FROM
    LLC <-- "<div style='background:transparent;'>APDUs<br>/<br>RAPDUs" -->EX

    EX <-- "<div style='background:transparent;'>Format amount<br>Address check" -->TO
    EX <-- "<div style='background:transparent;'>Format amount<br>Address check<br>Final transaction details" -->FROM
    FAKE -->EX
    EX <-- "<div style='background:transparent;'>User review" -->SCREEN
```
