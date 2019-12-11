#include "os.h"
#include "os_io_seproxyhal.h"

#ifndef _GLOBALS_H_
#define _GLOBALS_H_

#define P1_CONFIRM 0x01
#define P1_NON_CONFIRM 0x00
#define P1_FIRST 0x00
#define P1_MORE 0x80

#define FULL_ADDRESS_LENGTH 54
#define BIP32_PATH 5

extern ux_state_t ux;
// display stepped screens
extern unsigned int ux_step;
extern unsigned int ux_step_count;

extern const unsigned char CURVE_SIZE_BYTES;
extern const unsigned char PUB_KEY_LENGTH;
extern const unsigned char DER_SIGNATURE_LENGTH;

#endif
