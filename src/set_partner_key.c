#include <os.h>
#include <cx.h>

#include "globals.h"
#include "set_partner_key.h"
#include "swap_errors.h"
#include "globals.h"
#include "io.h"

int set_partner_key(const command_t *cmd) {
    // data is serialized as
    // 1 byte - partner name length L
    // L bytes - partner name
    // 65 bytes - uncompressed partner public key
    if (cmd->data.size < 1) {
        PRINTF("Error: Input buffer is too small\n");

        return reply_error(INCORRECT_COMMAND_DATA);
    }

    G_swap_ctx.partner.name_length = cmd->data.bytes[0];

    if ((G_swap_ctx.partner.name_length < MIN_PARTNER_NAME_LENGHT) ||
        (G_swap_ctx.partner.name_length > MAX_PARTNER_NAME_LENGHT)) {
        PRINTF("Error: Partner name length should be in [%u, %u]\n",
               MIN_PARTNER_NAME_LENGHT,
               MAX_PARTNER_NAME_LENGHT);

        return reply_error(INCORRECT_COMMAND_DATA);
    }

    if (1 + G_swap_ctx.partner.name_length + UNCOMPRESSED_KEY_LENGTH != cmd->data.size) {
        PRINTF("Error: Input buffer length doesn't match correct SET_PARTNER_KEY message\n");

        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // The incoming partner name is NOT NULL terminated, so we use memcpy and
    // manually NULL terminate the buffer
    memset(G_swap_ctx.partner.name, 0, sizeof(G_swap_ctx.partner.name));
    memcpy(G_swap_ctx.partner.name, cmd->data.bytes + 1, G_swap_ctx.partner.name_length);

    if (cmd->subcommand == SWAP) {
        if (cx_ecfp_init_public_key_no_throw(CX_CURVE_SECP256K1,
                                             cmd->data.bytes + 1 + G_swap_ctx.partner.name_length,
                                             UNCOMPRESSED_KEY_LENGTH,
                                             &(G_swap_ctx.partner.public_key)) != CX_OK) {
            PRINTF("Error: cx_ecfp_init_public_key_no_throw\n");
            return reply_error(INTERNAL_ERROR);
        }
    }

    if (cmd->subcommand == SELL || cmd->subcommand == FUND) {
        if (cx_ecfp_init_public_key_no_throw(CX_CURVE_256R1,
                                             cmd->data.bytes + 1 + G_swap_ctx.partner.name_length,
                                             UNCOMPRESSED_KEY_LENGTH,
                                             &(G_swap_ctx.partner.public_key)) != CX_OK) {
            PRINTF("Error: cx_ecfp_init_public_key_no_throw\n");
            return reply_error(INTERNAL_ERROR);
        }
    }

    cx_hash_sha256(cmd->data.bytes,
                   cmd->data.size,
                   G_swap_ctx.sha256_digest,
                   sizeof(G_swap_ctx.sha256_digest));

    if (reply_success() < 0) {
        PRINTF("Error: failed to send\n");

        return -1;
    }

    G_swap_ctx.state = PROVIDER_SET;

    return 0;
}
