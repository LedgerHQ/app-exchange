#ifndef _SWAP_ERRORS_H_
#define _SWAP_ERRORS_H_

// This value is the part of the host <-> device protocol
// they will be reported to host in APDU

// error codes tries to respect
// https://www.eftlab.com/knowledge-base/complete-list-of-apdu-responses/

typedef enum {
    INCORRECT_COMMAND_DATA = 0x6A80,
    DESERIALIZATION_FAILED = 0x6A81,
    WRONG_TRANSACTION_ID = 0x6A82,
    INVALID_ADDRESS = 0x6A83,
    USER_REFUSED = 0x6A84,
    INTERNAL_ERROR = 0x6A85,
    WRONG_P2 = 0x6A86,
    CLASS_NOT_SUPPORTED = 0x6E00,
    INVALID_INSTRUCTION = 0x6D00,
    SIGN_VERIFICATION_FAIL = 0x9D1A
} swap_error_e;

#endif  //_SWAP_ERRORS_H_