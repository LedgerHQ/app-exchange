# Transaction proposal format (protobuf)

The transaction proposal is a [protobuf 3](https://protobuf.dev/) payload (package `ledger_swap`).
This page describes that payload; the message used depends on the flow TYPE:

| Flow | TYPE                | Protobuf message                                |
| ---- | ------------------- | ----------------------------------------------- |
| SWAP | SWAP_LEGACY/SWAP_NEW | [`NewTransactionResponse`](#swap-newtransactionresponse) |
| SELL | SELL_LEGACY/SELL_NEW | [`NewSellResponse`](#sell-newsellresponse)      |
| FUND | FUND_LEGACY/FUND_NEW | [`NewFundResponse`](#fund-newfundresponse)      |

The canonical definition lives in
[`src/proto/protocol.proto`](https://github.com/LedgerHQ/app-exchange/blob/develop/src/proto/protocol.proto),
and the per-field maximum sizes in
[`src/proto/protocol.options`](https://github.com/LedgerHQ/app-exchange/blob/develop/src/proto/protocol.options).
The `.proto` snippets below are included directly from that source file, so they always reflect the
current schema.

!!! warning "Which fields must be set"
    Protobuf 3 marks every field as optional *on the wire*, but the application enforces its own
    requirements: it consumes some fields for the signature, the address checks and the on-screen
    review, and rejects the flow if a required field is missing or inconsistent. The **Requirement**
    column of each table below states what the application actually expects. The values are:

    - **Required** — the field must be set; omitting it makes the flow fail (rejected APDU, failed
      address/nonce check, or a wrong signature that the partner will not accept).
    - **Optional** — safely omitted; used only for the on-screen review or passed through as a memo.
    - **Conditional** — required only in specific cases; the row explains when.

## SWAP: `NewTransactionResponse`

```proto
--8<-- "src/proto/protocol.proto:new_transaction_response"
```

| Field                       | # | Type   | Max size | Requirement | Description                                                                                 |
| --------------------------- | - | ------ | -------- | ----------- | ------------------------------------------------------------------------------------------- |
| `payin_address`             | 1 | string | 151      | Required    | Address the FROM funds are sent to (the partner's deposit address). Signed by the FROM app. |
| `payin_extra_id`            | 2 | string | 20       | Conditional | Memo/tag/destination-tag for the payin address. Set at most one of `payin_extra_id` / `payin_extra_data` (see [Extra id vs extra data](#extra-id-vs-extra-data)). |
| `payin_extra_data`          | 13| bytes  | 37       | Conditional | Templated extra data blob, alternative to `payin_extra_id` (see [Extra id vs extra data](#extra-id-vs-extra-data)). |
| `refund_address`            | 3 | string | 151      | Required    | Address the FROM funds are refunded to if the swap fails. Checked to belong to the device (mismatch is fatal). |
| `refund_extra_id`           | 4 | string | 20       | Optional    | Memo/tag for the refund address, passed to the FROM app's address check.                    |
| `payout_address`            | 5 | string | 151      | Required    | Address the TO funds are credited to. Checked to belong to the device (mismatch triggers the cross-seed warning). |
| `payout_extra_id`           | 6 | string | 20       | Optional    | Memo/tag for the payout address, passed to the TO app's address check.                      |
| `currency_from`             | 7 | string | 10       | Required    | Ticker of the FROM currency; must match the FROM coin configuration (see [Currencies](#currencies)). |
| `currency_to`               | 8 | string | 10       | Required    | Ticker of the TO currency; must match the TO coin configuration (see [Currencies](#currencies)). |
| `amount_to_provider`        | 9 | bytes  | 16       | Required    | Amount of FROM sent to `payin_address`; signed by the FROM app (see [Amounts](#amounts)).   |
| `amount_to_wallet`          | 10| bytes  | 16       | Required    | Amount of TO credited to `payout_address`; shown on screen (see [Amounts](#amounts)).       |
| `device_transaction_id`     | 11| string | 11       | Conditional | Nonce, **required for SWAP_LEGACY only**: the 10-char string from `START_NEW_TRANSACTION`.   |
| `device_transaction_id_ng`  | 12| bytes  | 32       | Conditional | Nonce, **required for SWAP_NEW only**: the 32-byte value from `START_NEW_TRANSACTION`.       |

See [Device transaction id](#device-transaction-id) for which nonce field to set per flow.

## SELL: `NewSellResponse`

```proto
--8<-- "src/proto/protocol.proto:new_sell_response"
```

Legacy (SELL_LEGACY) and new (SELL_NEW) flows use the exact same message and field requirements.

| Field                   | # | Type       | Max size | Requirement | Description                                                             |
| ----------------------- | - | ---------- | -------- | ----------- | ----------------------------------------------------------------------- |
| `trader_email`          | 1 | string     | 50       | Optional    | Email of the trader (partner field `traderEmail`); shown on screen only. |
| `in_currency`           | 2 | string     | 10       | Required    | Ticker of the FROM currency; must match the coin configuration (partner field `inCurrency`). |
| `in_amount`             | 3 | bytes      | 16       | Required    | Amount of FROM sold; signed by the FROM app (partner field `inAmount`, see [Amounts](#amounts)). |
| `in_address`            | 4 | string     | 151      | Required    | Address the FROM funds are sent to; signed by the FROM app (partner field `account`).           |
| `in_extra_id`           | 8 | string     | 20       | Optional    | Memo/tag for `in_address`, passed to the FROM app (partner field `memo`).                       |
| `out_currency`          | 5 | string     | 10       | Required    | FIAT currency received (partner field `outCurrency`); shown on screen.                   |
| `out_amount`            | 6 | `UDecimal` | —        | Required    | FIAT amount received (partner field `outAmount`); shown on screen (see [UDecimal](#udecimal)). |
| `device_transaction_id` | 7 | bytes      | 32       | Required    | 32-byte nonce returned by `START_NEW_TRANSACTION`, checked by the application.                      |

## FUND: `NewFundResponse`

```proto
--8<-- "src/proto/protocol.proto:new_fund_response"
```

Legacy (FUND_LEGACY) and new (FUND_NEW) flows use the exact same message and field requirements.

| Field                   | # | Type   | Max size | Requirement | Description                                                             |
| ----------------------- | - | ------ | -------- | ----------- | ----------------------------------------------------------------------- |
| `user_id`               | 1 | string | 50       | Optional    | Identifier of the funding user; shown on screen only.                   |
| `account_name`          | 2 | string | 50       | Optional    | Human-readable name of the funded account (e.g. `Card 1234`); shown on screen only. |
| `in_currency`           | 3 | string | 10       | Required    | Ticker of the FROM currency; must match the coin configuration (partner field `inCurrency`). |
| `in_amount`             | 4 | bytes  | 16       | Required    | Amount of FROM funded; signed by the FROM app (partner field `inAmount`, see [Amounts](#amounts)). |
| `in_address`            | 5 | string | 151      | Required    | Address the FROM funds are sent to; signed by the FROM app (partner field `account`).           |
| `in_extra_id`           | 7 | string | 20       | Optional    | Memo/tag for `in_address`, passed to the FROM app (partner field `memo`).                       |
| `device_transaction_id` | 6 | bytes  | 32       | Required    | 32-byte nonce returned by `START_NEW_TRANSACTION`, checked by the application.                      |

## Encoding notes

### Field sizes

The **Max size** column of each table reports the value declared in
[`protocol.options`](https://github.com/LedgerHQ/app-exchange/blob/develop/src/proto/protocol.options),
which is the buffer size the application allocates for the field:

- For **string** fields the buffer includes the terminating null byte, so the maximum usable length
  is **one character less** than the listed size (e.g. `payin_address` accepts up to 150 characters,
  `currency_from` up to 9, the SWAP_LEGACY `device_transaction_id` up to 10).
- For **bytes** fields the listed size is the maximum number of bytes that can be sent.

### Amounts

All amount fields carried as `bytes` (`amount_to_provider`, `amount_to_wallet`, `in_amount`) are
**big-endian unsigned integers** expressed in the currency's smallest unit (e.g. wei, satoshi), with
a maximum of 16 bytes. The application trims leading zero bytes on reception, so `0x00 0x2A` and
`0x2A` are equivalent.

### UDecimal

The SELL `out_amount` uses the `UDecimal` helper message, which represents a decimal value as:

```proto
--8<-- "src/proto/protocol.proto:udecimal"
```

The value is `coefficient * 10^(-exponent)`, where `coefficient` is a big-endian unsigned integer
(max 16 bytes) and `exponent` a `uint32`. For example a `coefficient` of `12345` with `exponent` `2`
represents `123.45`.

### Device transaction id

The nonce returned by `START_NEW_TRANSACTION` **must** be echoed back in the proposal, and the
application rejects the flow (`WRONG_TRANSACTION_ID`) if it does not match. Which field carries it,
and its form, depends on the flow — this is the only field-level difference between a legacy flow and
its NG counterpart:

| Flow        | Field                      | Type   | Value                          |
| ----------- | -------------------------- | ------ | ------------------------------ |
| SWAP_LEGACY | `device_transaction_id`    | string | 10-char string                 |
| SWAP_NEW    | `device_transaction_id_ng` | bytes  | 32-byte value                  |
| SELL_LEGACY / SELL_NEW | `device_transaction_id` | bytes | 32-byte value             |
| FUND_LEGACY / FUND_NEW | `device_transaction_id` | bytes | 32-byte value             |

### Extra id vs extra data

For SWAP flows, `payin_extra_id` and `payin_extra_data` are **mutually exclusive** — providing both
is rejected (`WRONG_EXTRA_ID_OR_EXTRA_DATA`). Setting neither is valid and means the payin address
needs no extra id.

- `payin_extra_id` is a plain string memo/tag/destination-tag (e.g. XRP tag, Cosmos memo).
- `payin_extra_data` is a templated binary blob whose **first byte selects the template**:

    | Header byte | Template     | Total size |
    | ----------- | ------------ | ---------- |
    | `0x00`      | NATIVE       | 1 byte     |
    | `0x01`      | EVM_CALLDATA | 33 bytes (header + 32-byte hash)   |
    | `0x02`      | OP_RETURN    | 33 bytes (header + 32-byte hash)   |
    | `0x03`      | SOL_TEMPLATE | 37 bytes (header + 32-byte hash + 4-byte template id) |

    The application enforces the size matching the header byte. A lone `0x00` byte (NATIVE) is
    equivalent to sending no extra data. `payin_extra_data` is **not supported on Nano S**.

### Currencies

The crypto ticker fields — `currency_from` and `currency_to` (SWAP), and `in_currency` (SELL and
FUND) — are upper-cased by the application and mapped to the canonical Ledger currency name before
use. The SELL `out_currency` (a FIAT ticker) is displayed as received, without normalization.
