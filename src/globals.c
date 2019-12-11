#include "globals.h"
#include "os.h"

#ifdef TARGET_NANOX
#include "ux.h"
ux_state_t G_ux;
bolos_ux_params_t G_ux_params;
#else // TARGET_NANOX
ux_state_t ux;
#endif // TARGET_NANOX

// display stepped screens
unsigned int ux_step;
unsigned int ux_step_count;

const unsigned char CURVE_SIZE_BYTES = 32;
const unsigned char PUB_KEY_LENGTH = CURVE_SIZE_BYTES + 1;
const unsigned char DER_SIGNATURE_LENGTH = 6 + 2 * CURVE_SIZE_BYTES;

