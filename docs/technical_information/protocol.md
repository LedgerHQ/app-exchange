# EXCHANGE application protocol API

Communication is done through a series of request-response exchanges (APDU / RAPDU).

Please look at the [sequence diagram](./diagram.md) to know more about the APDUs used here.

## Request:

| Bytes    | Description                          |
| -------- | ------------------------------------ |
| 1 byte   | CLASS (constant 0xE0)                |
| 1 byte   | COMMAND to run                       |
| 1 byte   | P1: RATE_TYPE of the transaction     |
| 1 byte   | P2: TYPE and EXTENSION               |
| 1 byte   | LC: Length of the data section       |
| LC bytes | DATA, content depends of the COMMAND |


### COMMAND:

| Name                              | Value | Description                                                                                         |
| --------------------------------- | ----- | --------------------------------------------------------------------------------------------------- |
| GET_VERSION                       | 0x02  | Get application version. This APDU can be sent independently of the current app state               |
| START_NEW_TRANSACTION             | 0x03  | Start new EXCHANGE transaction. This APDU resets the app state                                      |
| SET_PARTNER_KEY                   | 0x04  | Set the credentials of the exchange partner                                                         |
| CHECK_PARTNER                     | 0x05  | Check that the credentials of the exchange partner are signed by the Ledger key                     |
| PROCESS_TRANSACTION_RESPONSE      | 0x06  | Receive the transaction proposal from the exchange partner                                          |
| CHECK_TRANSACTION_SIGNATURE       | 0x07  | Check that the transaction proposal is signed by the exchange partner                               |
| GET_CHALLENGE                     | 0x10  | Optional: Retrieve the current challenge value for the TLV trusted descriptor feature               |
| SEND_TRUSTED_NAME_DESCRIPTOR      | 0x11  | Optional: Provide a TLV trusted descriptor                                                          |
| CHECK_ASSET_IN_LEGACY_AND_DISPLAY | 0x08  | Format the amounts and fees used and prompts screen review (FUND_LEGACY and SELL_LEGACY flows only) |
| CHECK_ASSET_IN_AND_DISPLAY        | 0x0B  | Format the amounts and fees used and prompts screen review (FUND based and SELL based flows)        |
| CHECK_ASSET_IN_NO_DISPLAY         | 0x0D  | Format the amounts and fees used. (FUND based and SELL based flows only)                            |
| CHECK_PAYOUT_ADDRESS              | 0x08  | Check that the payout address belongs to us (SWAP based flows only)                                 |
| CHECK_REFUND_ADDRESS_AND_DISPLAY  | 0x09  | Check that the refund address belongs to us (SWAP based flows only) and prompts screen review       |
| CHECK_REFUND_ADDRESS_NO_DISPLAY   | 0x0C  | Check that the refund address belongs to us (SWAP based flows only)                                 |
| PROMPT_UI_DISPLAY                 | 0x0F  | Prompt the screen review for the user                                                               |
| START_SIGNING_TRANSACTION         | 0x0A  | Start the library application responsible for the FROM signing                                      |

The COMMANDS must be sent to the application in the correct order, this order depends of the TYPE chosen for the exchange flow:

| All types                    |
| ---------------------------- |
| START_NEW_TRANSACTION        |
| SET_PARTNER_KEY              |
| CHECK_PARTNER                |
| PROCESS_TRANSACTION_RESPONSE |
| CHECK_TRANSACTION_SIGNATURE  |

| SWAP based TYPES                | or (discouraged version)         | FUND based and SELL based TYPES | or (discouraged version)   |
| ------------------------------- | -------------------------------- | ------------------------------- | ---------------------------|
| CHECK_PAYOUT_ADDRESS            | CHECK_PAYOUT_ADDRESS             | CHECK_ASSET_IN_NO_DISPLAY       | CHECK_ASSET_IN_AND_DISPLAY |
| CHECK_REFUND_ADDRESS_NO_DISPLAY | CHECK_REFUND_ADDRESS_AND_DISPLAY | PROMPT_UI_DISPLAY               |                            |
| PROMPT_UI_DISPLAY               |                                  |                                 |                            |

| All types                 |
| ------------------------- |
| START_SIGNING_TRANSACTION |

#### Notes on COMMANDS:

- Command START_SIGNING_TRANSACTION requires that a UI review by the user has happened, either through a CHECK_X_AND_DISPLAY (legacy method), or through the dedicated PROMPT_UI_DISPLAY command.

- It is always possible to restart the flow by sending a START_NEW_TRANSACTION command, except when the UI review screen is being displayed.

- The command START_SIGNING_TRANSACTION will start the library application, the current application will not be EXCHANGE anymore.

### RATE_TYPE:

Different possible rates for the transaction. The rate is sent to the app as P1 of an APDU.

| Name     | Value | Description                                  |
| -------- | ----- | -------------------------------------------- |
| FIXED    | 0x00  | The rate in the transaction is a fixed value |
| FLOATING | 0x01  | The rate in the transaction is an estimation |


### TYPE:

Different exchange types are possible for the app. The type is sent to the app as the lowest 4 bits of the P2 byte of the APDU.

Changing the subcommand after an exchange flow is started will result in an error response and the APDU is ignored.

| Name        | Value | Description                                                                                                       |
| ----------- | ----- | ----------------------------------------------------------------------------------------------------------------- |
| SWAP_LEGACY | 0x00  | SWAP transaction (crypto against crypto) using legacy signature and encoding, deprecated by the NEW counterpart   |
| SELL_LEGACY | 0x01  | SELL transaction (crypto against fiat) using legacy signature and encoding, deprecated by the NEW counterpart     |
| FUND_LEGACY | 0x02  | FUND transaction (crypto to owned account) using legacy signature and encoding, deprecated by the NEW counterpart |
| SWAP_NEW    | 0x03  | SWAP transaction (crypto against crypto) using unified signature and encoding                                     |
| SELL_NEW    | 0x04  | SELL transaction (crypto against fiat) using unified signature and encoding                                       |
| FUND_NEW    | 0x05  | FUND transaction (crypto to owned account) using unified signature and encoding                                   |


### EXTENSION:

This feature is only available in a PROCESS_TRANSACTION_RESPONSE command in a SWAP_NEW, SELL_NEW, or FUND_NEW flow.

In Legacy flows the extension must be P2_NONE.

The extension is sent to the app as the upper 4 bits of the P2 byte of the APDU.

The maximum DATA in a single APDU is 255 bytes, in case it is not sufficient for a command,
it is possible to use the EXTENSION feature to send the command in several parts.

To use the EXTENSION feature, craft the data of the command you want to send and split it in 255 bytes chunks.

Then send this chunks to the app using a combination of P2_EXTEND and P2_MORE in each APDU header.

The application will reconstruct the DATA by concatenating the received APDUs.

The application will refuse to reconstruct more than 512 bytes.

| Name      | Value     | Description                                                       |
| --------- | --------- | ----------------------------------------------------------------- |
| P2_NONE   | 0x00 << 4 | This APDU is self sufficient                                      |
| P2_EXTEND | 0x01 << 4 | This APDU is not whole, it extends a previously received one      |
| P2_MORE   | 0x02 << 4 | This APDU is not whole, the followup part while be received later |

### DATA:

#### GET_VERSION

No data expected.

#### START_NEW_TRANSACTION

No data expected.

#### SET_PARTNER_KEY

##### For all LEGACY TYPES, the data for this command is:

| Bytes              | Description                          |
| ------------------ | ------------------------------------ |
| 1 byte             | Length N of the encoded partner name |
| N bytes            | Partner name encoded with utf-8      |
| LC - (1 + N) bytes | Partner public key                   |

##### For all UNIFIED TYPES, the data for this command is:

| Bytes              | Description                          |
| ------------------ | ------------------------------------ |
| 1 byte             | Length N of the encoded partner name |
| N bytes            | Partner name encoded with utf-8      |
| 1 byte             | Curve used by the partner            |
| LC - (2 + N) bytes | Partner public key                   |

With the possible values for the curve being 0x00 for SECP256K1, and 0x01 for SECP256R1.

#### CHECK_PARTNER

| Bytes    | Description                                                                             |
| -------- | --------------------------------------------------------------------------------------- |
| LC bytes | Signature of the partner credentials by the Ledger key, curve secp256k1 hashfunc sha256 |

#### PROCESS_TRANSACTION_RESPONSE

Please refer to the src/protobuf files for the actual transaction proposal content.

##### For all LEGACY TYPES, the data for this command is:

| Bytes   | Description                                                                                                 |
| ------- | ----------------------------------------------------------------------------------------------------------- |
| 1 byte  | Length N of the encoded transaction proposal                                                                |
| N bytes | Transaction proposal. Bytes array for SWAP_LEGACY, URLsafe base 64 encoding for SELL_LEGACY and FUND_LEGACY |
| 1 byte  | Length M of the transaction fees                                                                            |
| M bytes | Transaction fees                                                                                            |

##### For all UNIFIED TYPES, the data for this command is:

| Bytes   | Description                                  |
| ------- | -------------------------------------------- |
| 1 byte  | Format used for the transaction encoding     |
| 2 bytes | Length N of the encoded transaction proposal |
| N bytes | Encoded transaction proposal                 |
| 1 byte  | Length M of the transaction fees             |
| M bytes | Transaction fees                             |

With the possible values for the format being 0x00 for Bytes Array (no encoding), and 0x01 for Base 64 Url encoding.

The DATA of this command may exceed the capacity of a single APDU (255 bytes), in this case use the EXTENSION feature.

#### GET_CHALLENGE

Retrieve the current challenge value for the TLV trusted descriptor feature.

It will be regenerated on application side following a SEND_TRUSTED_NAME_DESCRIPTOR command (successful or not).

#### SEND_TRUSTED_NAME_DESCRIPTOR

Provide a TLV trusted descriptor from the CAL to apply a trusted value upon the refund or payout address.

#### CHECK_TRANSACTION_SIGNATURE

##### For all LEGACY TYPES, the data for this command is:

| Bytes    | Description                                                   |
| -------- | ------------------------------------------------------------- |
| LC bytes | Signature of the computed transaction proposed by the partner |

For SWAP_LEGACY TYPE, the signature is computed on the transaction proposal.

For SELL_LEGACY and FUND_LEGACY the signature is computed on the transaction proposal prefixed with a DOT ('.').

For SWAP_LEGACY and FUND_LEGACY, the signature is in DER format.

For SELL_LEGACY the signature is in (R,S) format.

##### For all UNIFIED TYPES, the data for this command is:

| Bytes        | Description                                                   |
| ------------ | ------------------------------------------------------------- |
| 1 byte       | If the signature is computed on a prefixed transaction        |
| 1 byte       | Format of the signature itself                                |
| LC - 2 bytes | Signature of the computed transaction proposed by the partner |

With the possible values for the format of the transaction used for signing being 0x01 if it was DOT ('.') prefixed, 0x00 otherwise.

With the possible values for the format of the signature itself being 0x00 for DER format, and 0x01 for (R,S) format.

#### CHECK_ASSET_IN_LEGACY_AND_DISPLAY

This command is DEPRECATED.

Please refer to CHECK_ASSET_IN_AND_DISPLAY (strict equivalent but discouraged) or CHECK_ASSET_IN_NO_DISPLAY + PROMPT_UI_DISPLAY

This command works only for the SELL_LEGACY and FUND_LEGACY TYPES, the data content is the same as CHECK_ASSET_IN_AND_DISPLAY only the INS byte is different (and does not collide with CHECK_PAYOUT_ADDRESS).

#### CHECK_ASSET_IN_AND_DISPLAY

This command is the same as CHECK_ASSET_IN_NO_DISPLAY except that the application will prompt the UI review if the check is successful.

Usage of this command is discouraged, please use CHECK_ASSET_IN_NO_DISPLAY + PROMPT_UI_DISPLAY instead.

#### CHECK_ASSET_IN_NO_DISPLAY

This command is used for SELL based and FUND based TYPES.

| Bytes   | Description                                                                                                    |
| ------- | -------------------------------------------------------------------------------------------------------------- |
| 1 byte  | Coin configuration length of the FROM coin. The coin configuration is made of the ticker, appname, and subconf |
| 1 byte  | Ticker name length N                                                                                           |
| N bytes | Ticker name of this the coin configuration. The ticker has to be the same as the FROM ticker                   |
| 1 byte  | Application name length M                                                                                      |
| M bytes | Name of the application that can handle this currency                                                          |
| 1 byte  | Sub coin configuration length R                                                                                |
| R bytes | Sub coin configuration, used for tokens to specify an app the subticker and the decimals                       |
| S bytes | Signature of the coin configuration by the Ledger key in DER format, curve secp256k1 hashfunc sha256           |
| 1 byte  | Packed derivation path length T                                                                                |
| T bytes | Packed derivation path used for the FROM coin                                                                  |

#### CHECK_PAYOUT_ADDRESS

This command is used only in the SWAP_LEGACY and SWAP_NEW TYPES.

| Bytes   | Description                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------ |
| 1 byte  | Coin configuration length of the TO coin. The coin configuration is made of the ticker, appname, and subconf |
| 1 byte  | Ticker name length N                                                                                         |
| N bytes | Ticker name of this the coin configuration. The ticker has to be the same as the TO ticker                   |
| 1 byte  | Application name length M                                                                                    |
| M bytes | Name of the application that can handle this currency                                                        |
| 1 byte  | Sub coin configuration length R                                                                              |
| R bytes | Sub coin configuration, used for tokens to specify an app the subticker and the decimals                     |
| S bytes | Signature of the coin configuration by the Ledger key in DER format, curve secp256k1 hashfunc sha256         |
| 1 byte  | Packed derivation path length T                                                                              |
| T bytes | Packed derivation path used for the TO coin                                                                  |

#### CHECK_REFUND_ADDRESS_AND_DISPLAY

This command is the same as CHECK_REFUND_ADDRESS_NO_DISPLAY except that the application will prompt the UI review if the check is successful.

Usage of this command is discouraged, please use CHECK_REFUND_ADDRESS_NO_DISPLAY + PROMPT_UI_DISPLAY instead.

#### CHECK_REFUND_ADDRESS_NO_DISPLAY

This command is used only in the SWAP_LEGACY and SWAP_NEW TYPES.
<!-- --8<-- [start:coin_configuration] -->

| Bytes   | Description                                                                                                    |
| ------- | -------------------------------------------------------------------------------------------------------------- |
| 1 byte  | Coin configuration length of the FROM coin. The coin configuration is made of the ticker, appname, and subconf |
| 1 byte  | Ticker name length N                                                                                           |
| N bytes | Ticker name of this the coin configuration. The ticker has to be the same as the FROM ticker                   |
| 1 byte  | Application name length M                                                                                      |
| M bytes | Name of the application that can handle this currency                                                          |
| 1 byte  | Sub coin configuration length R                                                                                |
| R bytes | Sub coin configuration, used for tokens to specify an app the subticker and the decimals                       |
| S bytes | Signature of the coin configuration by the Ledger key in DER format, curve secp256k1 hashfunc sha256           |
| 1 byte  | Packed derivation path length T                                                                                |
| T bytes | Packed derivation path used for the FROM coin                                                                  |
<!-- --8<-- [end:coin_configuration] -->

#### PROMPT_UI_DISPLAY

This command prompts the UI so the user can validate the transaction on screen.

#### START_SIGNING_TRANSACTION

No data expected.


## Response:

| Bytes         | Description           |
| ------------- | --------------------- |
| N bytes       | Command specific data |
| 2 bytes       | Return code           |

### Returned data

Only the COMMANDS described below return data. All others only return a code.

#### GET_VERSION

In case of success, this command will return the application version in format {MAJOR.MINOR.PATCH}.

#### START_NEW_TRANSACTION

In case of success, this command will return a nonce called "device transaction id" used for the initiated flow.

For TYPE SWAP_LEGACY, the format of this nonce is a 10 char array.

For all other TYPES, the format of this nonce is a 32 bytes array.

#### GET_CHALLENGE

The current challenge value in u32 format.

### Return code

Return code can be one of the following values:

| Bytes  | Name                         | Description                                                                             |
| ------ | ---------------------------- | --------------------------------------------------------------------------------------- |
| 0x6A80 | INCORRECT_COMMAND_DATA       | The DATA sent does not match the correct format for the COMMAND specified               |
| 0x6A81 | DESERIALIZATION_FAILED       | Can't parse partner transaction proposal                                                |
| 0x6A82 | WRONG_TRANSACTION_ID         | Transaction ID is not equal to one generated on the START_NEW_TRANSACTION step          |
| 0x6A83 | INVALID_ADDRESS              | Refund or payout address doesn't belong to us                                           |
| 0x6A84 | USER_REFUSED_TRANSACTION     | User refused the transaction proposal                                                   |
| 0x6A85 | INTERNAL_ERROR               | Internal error of the application                                                       |
| 0x6A86 | WRONG_P1                     | The P1 value is not a valid RATE                                                        |
| 0x6A87 | WRONG_P2_SUBCOMMAND          | The P2 lower 4 bits of the P2 byte is not a valid SUBCOMMAND                            |
| 0x6A88 | WRONG_P2_EXTENSION           | The P2 upper 4 bits of the P2 byte is not a valid EXTENSION                             |
| 0x6A89 | INVALID_P2_EXTENSION         | The extension is a valid value but is refused in the current context                    |
| 0x6A8A | MEMORY_CORRUPTION            | A child application started by Exchange has corrupted the Exchange application memory   |
| 0x6A8B | AMOUNT_FORMATTING_FAILED     | A child application failed to format an amount provided by the partner                  |
| 0x6A8C | APPLICATION_NOT_INSTALLED    | The requested child application is not installed on the device                          |
| 0x6A8D | WRONG_EXTRA_ID_OR_EXTRA_DATA | The values given for extra_id (memo) and / or extra_data (Thorswap like) are incorrect  |
| 0x6A8E | WRONG_TLV_CHALLENGE          | The challenge provided in the descriptor does not match the challenge generated         |
| 0x6A8F | WRONG_TLV_CONTENT            | The content of the descriptor does not fit the Exchange use case specification          |
| 0x6A90 | MISSING_TLV_CONTENT          | The descriptor is missing requirement tags                                              |
| 0x6A91 | WRONG_TRUSTED_NAME_TLV       | The content of the descriptor does not fit the common descriptor specification          |
| 0x6A92 | USER_REFUSED_CROSS_SEED      | User refused the transaction proposal when prompted by the Cross Seed Swap warning      |
| 0x6E00 | CLASS_NOT_SUPPORTED          | The CLASS is not 0xE0                                                                   |
| 0x6E01 | MALFORMED_APDU               | The APDU header is malformed                                                            |
| 0x6E02 | INVALID_DATA_LENGTH          | The length of the DATA is refused for this COMMAND                                      |
| 0x6D00 | INVALID_INSTRUCTION          | COMMAND is not in the "Possible commands" table                                         |
| 0x6D01 | UNEXPECTED_INSTRUCTION       | COMMAND is in the "Possible commands" table but is refused in the current context       |
| 0x6D02 | DESCRIPTOR_NOT_USED          | The received descriptor could not be applied to refund nor payout address               |
| 0x9D1A | SIGN_VERIFICATION_FAIL       | The signature sent by this command does not match the data or the associated public key |
| 0x9000 | SUCCESS                      | Success code                                                                            |
