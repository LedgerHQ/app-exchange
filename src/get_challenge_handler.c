#include <cx.h>
#include "get_challenge_handler.h"
#include "swap_errors.h"
#include "buffer.h"
#include "io.h"
#include "globals.h"

static uint32_t challenge;

/**
 * Generate a new challenge from the Random Number Generator
 */
void roll_challenge(void) {
#ifdef FIXED_TLV_CHALLENGE
    challenge = 0xdeadbeef;
#else
    challenge = cx_rng_u32();
#endif
}

/**
 * Get the current challenge
 *
 * @return challenge
 */
uint32_t get_challenge(void) {
    return challenge;
}

/**
 * Send back the current challenge
 */
int get_challenge_handler(void) {
    PRINTF("New challenge -> %u\n", challenge);
    uint8_t output_buffer[4];
    U4BE_ENCODE(output_buffer, 0, challenge);

    buffer_t output;
    output.ptr = output_buffer;
    output.size = 4;
    output.offset = 0;

    if (io_send_response_buffers(&output, 1, SUCCESS) < 0) {
        return -1;
    }

    return 0;
}
