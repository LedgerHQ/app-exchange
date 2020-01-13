#ifndef _COMMANDS_H_
#define _COMMANDS_H_
// commands
typedef enum  {
    GET_VERSION_COMMAND                     = 0x00,
    START_NEW_TRANSACTION_COMMAND           = 0x01,
    SET_PARTNER_KEY_COMMAND                 = 0x02,
    PROCESS_TRANSACTION_RESPONSE_COMMAND    = 0x03,
    CHECK_TRANSACTION_SIGNATURE_COMMAND     = 0x04,
    CHECK_PAYOUT_ADDRESS                    = 0x05,
    CHECK_REFUND_ADDRESS                    = 0x06,
    USER_VALIDATION_RESPONSE                = 0x07,
    COMMAND_UPPER_BOUND
} command_e;

#endif //_COMMANDS_H_