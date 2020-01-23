#include "globals.h"
#include "os.h"

#ifdef TARGET_NANOX
#include "ux.h"
ux_state_t G_ux;
bolos_ux_params_t G_ux_params;
#else // TARGET_NANOX
ux_state_t ux;
#endif // TARGET_NANOX

const unsigned char CURVE_SIZE_BYTES = 32;
const unsigned char PUB_KEY_LENGTH = CURVE_SIZE_BYTES + 1;
const unsigned char UNCOMPRESSED_KEY_LENGTH = CURVE_SIZE_BYTES * 2U + 1;
const unsigned char MAX_DER_SIGNATURE_LENGTH = 6 + 2 * (CURVE_SIZE_BYTES + 1);
const unsigned char MIN_DER_SIGNATURE_LENGTH = 6 + 2 * (CURVE_SIZE_BYTES);
