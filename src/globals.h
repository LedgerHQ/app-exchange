#ifndef _GLOBALS_H_
#define _GLOBALS_H_

#include "os.h"
#include "os_io_seproxyhal.h"

#define P1_CONFIRM 0x01
#define P1_NON_CONFIRM 0x00
#define P1_FIRST 0x00
#define P1_MORE 0x80

#define CURVE_SIZE_BYTES    32U
#define PUB_KEY_LENGTH      33U
#define UNCOMPRESSED_KEY_LENGTH 65U
#define MAX_DER_SIGNATURE_LENGTH 74U
#define MIN_DER_SIGNATURE_LENGTH 70U

#endif
