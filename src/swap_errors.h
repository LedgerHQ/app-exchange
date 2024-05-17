#pragma once

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
    WRONG_P1 = 0x6A86,
    WRONG_P2_SUBCOMMAND = 0x6A87,
    WRONG_P2_EXTENSION = 0x6A88,
    INVALID_P2_EXTENSION = 0x6A89,
    MEMORY_CORRUPTION = 0x6A8A,
    AMOUNT_FORMATTING_FAILED = 0x6A8B,
    CLASS_NOT_SUPPORTED = 0x6E00,
    MALFORMED_APDU = 0x6E01,
    INVALID_DATA_LENGTH = 0x6E02,
    INVALID_INSTRUCTION = 0x6D00,
    UNEXPECTED_INSTRUCTION = 0x6D01,
    SIGN_VERIFICATION_FAIL = 0x9D1A,
    SUCCESS = 0x9000,
} swap_error_e;
