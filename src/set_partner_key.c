#include "set_partner_key.h"
#include "os.h"
#include "swap_errors.h"
#include "globals.h"
#include "reply_error.h"

int set_partner_key(subcommand_e subcommand,                                        //
                    swap_app_context_t *ctx,                                        //
                    unsigned char *input_buffer, unsigned int input_buffer_length,  //
                    SendFunction send) {
    // data is serialized as
    // 1 byte - partner name length L
    // L bytes - partner name
    // 65 bytes - uncompressed partner public key
    if (input_buffer_length < 1) {
        PRINTF("Error: Input buffer is too small");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    ctx->partner.name_length = input_buffer[0];

    if ((ctx->partner.name_length < 3) || (ctx->partner.name_length > 15)) {
        PRINTF("Error: Partner name length should be in [3, 15]");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    if (1 + ctx->partner.name_length + UNCOMPRESSED_KEY_LENGTH != input_buffer_length) {
        PRINTF("Error: Input buffer length doesn't correspond to correct SET_PARTNER_KEY message");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    os_memcpy(ctx->partner.name, input_buffer + 1, ctx->partner.name_length);

    if (subcommand == SWAP) {
        cx_ecfp_init_public_key(CX_CURVE_SECP256K1, input_buffer + 1 + ctx->partner.name_length,
                                UNCOMPRESSED_KEY_LENGTH, &(ctx->partner.public_key));
    }

    if (subcommand == SELL) {
        cx_ecfp_init_public_key(CX_CURVE_256R1, input_buffer + 1 + ctx->partner.name_length,
                                UNCOMPRESSED_KEY_LENGTH, &(ctx->partner.public_key));
    }

    cx_hash_sha256(input_buffer, input_buffer_length, ctx->sha256_digest,
                   sizeof(ctx->sha256_digest));

    unsigned char ouput_buffer[2] = {0x90, 0x00};

    if (send(ouput_buffer, 2) < 0) {
        PRINTF("Error: failed to send");

        return -1;
    }

    ctx->state = PROVIDER_SET;

    return 0;
}
