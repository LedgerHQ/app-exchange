#ifndef _COMMANDS_H
#define _COMMANDS_H
// commands
typedef enum  {
    GET_VERSION_COMMAND                     = 0x01,
    START_NEW_TRANSACTION_COMMAND           = 0x02,
    SET_PARTNER_KEY_COMMAND                 = 0x03,
    PROCESS_TRANSACTION_RESPONSE_COMMAND    = 0x04,
    CHECK_TRANSACTION_SIGNATURE_COMMAND     = 0x05,
    COMMAND_UPPER_BOUND
} command_e;

#endif //_COMMANDS_H