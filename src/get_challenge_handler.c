#include <cx.h>
#include "get_challenge_handler.h"
#include "swap_errors.h"
#include "buffer.h"
#include "io.h"
#include "globals.h"

static uint32_t challenge;

#define LAST_BYTE_MASK 0x000000FF

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
    output_buffer[0] = (uint8_t) ((challenge >> 24) & LAST_BYTE_MASK);
    output_buffer[1] = (uint8_t) ((challenge >> 16) & LAST_BYTE_MASK);
    output_buffer[2] = (uint8_t) ((challenge >> 8) & LAST_BYTE_MASK);
    output_buffer[3] = (uint8_t) (challenge & LAST_BYTE_MASK);

    buffer_t output;
    output.ptr = output_buffer;
    output.size = 4;
    output.offset = 0;

    if (io_send_response_buffers(&output, 1, SUCCESS) < 0) {
        return -1;
    }

    return 0;
}
