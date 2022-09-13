#include <os.h>
#include <cx.h>

#include "swap_app_context.h"
#include "set_partner_key.h"
#include "swap_errors.h"
#include "globals.h"
#include "reply_error.h"

int set_partner_key(swap_app_context_t *ctx, const command_t *cmd, SendFunction send) {
    // data is serialized as
    // 1 byte - partner name length L
    // L bytes - partner name
    // 65 bytes - uncompressed partner public key
    if (cmd->data.size < 1) {
        PRINTF("Error: Input buffer is too small\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    ctx->partner.name_length = cmd->data.bytes[0];

    if ((ctx->partner.name_length < MIN_PARTNER_NAME_LENGHT) ||
        (ctx->partner.name_length > MAX_PARTNER_NAME_LENGHT)) {
        PRINTF("Error: Partner name length should be in [%u, %u]\n",
               MIN_PARTNER_NAME_LENGHT,
               MAX_PARTNER_NAME_LENGHT);

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    if (1 + ctx->partner.name_length + UNCOMPRESSED_KEY_LENGTH != cmd->data.size) {
        PRINTF("Error: Input buffer length doesn't match correct SET_PARTNER_KEY message\n");

        return reply_error(ctx, INCORRECT_COMMAND_DATA, send);
    }

    // The incoming partner name is NOT NULL terminated, so we use memcpy and
    // manually NULL terminate the buffer
    memset(ctx->partner.name, 0, sizeof(ctx->partner.name));
    memcpy(ctx->partner.name, cmd->data.bytes + 1, ctx->partner.name_length);

    if (cmd->subcommand == SWAP) {
        cx_ecfp_init_public_key(CX_CURVE_SECP256K1,
                                cmd->data.bytes + 1 + ctx->partner.name_length,
                                UNCOMPRESSED_KEY_LENGTH,
                                &(ctx->partner.public_key));
    }

    if (cmd->subcommand == SELL || cmd->subcommand == FUND) {
        cx_ecfp_init_public_key(CX_CURVE_256R1,
                                cmd->data.bytes + 1 + ctx->partner.name_length,
                                UNCOMPRESSED_KEY_LENGTH,
                                &(ctx->partner.public_key));
    }

    cx_hash_sha256(cmd->data.bytes, cmd->data.size, ctx->sha256_digest, sizeof(ctx->sha256_digest));

    unsigned char ouput_buffer[2] = {0x90, 0x00};

    if (send(ouput_buffer, 2) < 0) {
        PRINTF("Error: failed to send\n");

        return -1;
    }

    ctx->state = PROVIDER_SET;

    return 0;
}
