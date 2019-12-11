#ifndef _ERRORS_H_
#define _ERRORS_H_

// error codes trys to respect https://www.eftlab.com/knowledge-base/complete-list-of-apdu-responses/

#define OUTPUT_BUFFER_IS_TOO_SMALL 0x6000
#define INCORRECT_COMMAND_DATA 0x6A80
#define DESERIALIZATION_FAILED 0x6A81
#define WRONG_TRANSACTION_ID 0x6A82
#define CLASS_NOT_SUPPORTED 0x6E00
#define INVALID_INSTRUCTION 0x6D00
#define SIGN_VERIFICATION_FAIL 0x9D1A

#endif //_ERRORS_H_