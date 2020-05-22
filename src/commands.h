#ifndef _COMMANDS_H_
#define _COMMANDS_H_
// commands
typedef enum  {
    GET_VERSION_COMMAND                     = 0x00,
    START_NEW_TRANSACTION_COMMAND           = 0x01,
    SET_PARTNER_KEY_COMMAND                 = 0x02,
    CHECK_PARTNER_COMMAND                   = 0x03,
    PROCESS_TRANSACTION_RESPONSE_COMMAND    = 0x04,
    CHECK_TRANSACTION_SIGNATURE_COMMAND     = 0x05,
    CHECK_PAYOUT_ADDRESS                    = 0x06,
    CHECK_REFUND_ADDRESS                    = 0x07,
    START_SIGNING_TRANSACTION               = 0x08,
    COMMAND_UPPER_BOUND
} command_e;

#endif //_COMMANDS_H_