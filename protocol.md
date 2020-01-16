# Protocol to speak with EXCHANGE application
Communication is done in request-response maner.
### Request:
| Bytes         | Meaning       |
| ------------- | ------------- |
| 0xE0          | Universal constant |
| COMMAND       | Byte for command, each command is described below |
| 0x00 | not used |
| 0x00 | not used |
| N bytes | command data, depends on specific command|



Posible commands:

| Name | Value | Description |
| ---- | ----- | ----------- |
| GET_VERSION_COMMAND           | 0x00 | Get application version |
| START_NEW_TRANSACTION_COMMAND | 0x01 | Start new EXCHANGE transaction |
| SET_PARTNER_KEY_COMMAND       | 0x02 | Set partner public key |
| PROCESS_TRANSACTION_RESPONS   | 0x03 | Process transaction received from partner|
| CHECK_TRANSACTION_SIGNATURE   | 0x04 | Check signature of partner transaction |
| CHECK_PAYOUT_ADDRES           | 0x05 | Check that payout address belong to us |
| CHECK_REFUND_ADDRES           | 0x06 | Check that refund address belong to us |
### Response:
| Bytes         | Meaning       |
| ------------- | ------------- |
| N bytes       | Command specific data |
| 2 bytes       | Result |

Result can be one of the following sequences:
| Bytes | Name | Description |
| ----- | ---- | ----------- |
| 0x6A80 | INCORRECT_COMMAND_DATA   | Command byte, or specific command data is incorrect |
| 0x6A81 | DESERIALIZATION_FAILED   | Can't parse partner transaction |
| 0x6A82 | WRONG_TRANSACTION_ID     | Transaction ID is not equal to one generated on the first step|
| 0x6A83 | INVALID_ADDRESS          | Refund or payout address doesn't belong to us |
| 0x6A84 | USER_REFUSED             | User refused transaction |
| 0x6A85 | INTERNAL_ERROR           | Some error inside the device application |
| 0x6E00 | CLASS_NOT_SUPPORTED      | |
| 0x6D00 | INVALID_INSTRUCTION      | Command byte is not the one from the "Possible commands" table |
| 0x9D1A | SIGN_VERIFICATION_FAIL   | Signature is incorrect |
| 0x9000 | SUCCESS                  | Success |

## Start new transaction
This should be the first command
On this step device will generate 10 capital latin letters and return it to the the host application.

No command data expected in this command request.

In case of success command specific data in response contains 10 bytes - representation of transaction ID.

## Set partner key
Partner public key and partner name signed by Ledger private key is send in this command. This command is only allowed after successful return from `START_NEW_TRANSACTION_COMMAND`
