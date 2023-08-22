#include <os.h>
#include <cx.h>

#include "globals.h"
#include "set_partner_key.h"
#include "swap_errors.h"
#include "globals.h"
#include "buffer.h"
#include "io.h"
#include "cx.h"

static uint16_t parse_set_partner_key_command(const command_t *cmd,
                                              buf_t *partner_name,
                                              uint8_t **raw_pubkey) {
    // data is serialized as
    // 1 byte - partner name length L
    // L bytes - partner name
    // 65 bytes - uncompressed partner public key
    uint16_t offset = 0;
    if (!parse_to_sized_buffer(cmd->data.bytes, cmd->data.size, 1, partner_name, &offset)) {
        PRINTF("Failed to read partner name from partner credentials\n");
        return INCORRECT_COMMAND_DATA;
    }

    if ((partner_name->size < MIN_PARTNER_NAME_LENGHT) ||
        (partner_name->size > MAX_PARTNER_NAME_LENGHT)) {
        PRINTF("Error: Partner name length should be in [%u, %u]\n",
               MIN_PARTNER_NAME_LENGHT,
               MAX_PARTNER_NAME_LENGHT);
        return INCORRECT_COMMAND_DATA;
    }

    if (offset + UNCOMPRESSED_KEY_LENGTH != cmd->data.size) {
        PRINTF("Error: Input buffer length doesn't match correct SET_PARTNER_KEY message\n");
        return INCORRECT_COMMAND_DATA;
    }
    *raw_pubkey = cmd->data.bytes + offset;

    return 0;
}

int set_partner_key(const command_t *cmd) {
    // Use dedicated function to extract the partner name and public key
    buf_t partner;
    uint8_t *raw_pubkey;
    uint16_t err = parse_set_partner_key_command(cmd, &partner, &raw_pubkey);
    if (err != 0) {
        return reply_error(err);
    }

    // The incoming partner name is NOT NULL terminated, so we use memcpy and
    // manually NULL terminate the buffer
    memset(G_swap_ctx.partner.name, 0, sizeof(G_swap_ctx.partner.name));
    memcpy(G_swap_ctx.partner.name, partner.bytes, partner.size);
    G_swap_ctx.partner.name_length = partner.size;

    // Create the verifying key from the raw public key. Curve used depends of the flow
    cx_curve_t curve;
    if (cmd->subcommand == SWAP) {
        curve = CX_CURVE_SECP256K1;
    } else {
        curve = CX_CURVE_256R1;
    }
    if (cx_ecfp_init_public_key_no_throw(curve,
                                         raw_pubkey,
                                         UNCOMPRESSED_KEY_LENGTH,
                                         &(G_swap_ctx.partner.public_key)) != CX_OK) {
        PRINTF("Error: cx_ecfp_init_public_key_no_throw\n");
        return reply_error(INTERNAL_ERROR);
    }

    // Save the hash of the entire credentials to check that the Ledger key signed it later
    if (cx_hash_sha256(cmd->data.bytes,
                       cmd->data.size,
                       G_swap_ctx.sha256_digest,
                       sizeof(G_swap_ctx.sha256_digest)) == 0) {
        PRINTF("cx_hash_sha256 internal error\n");
        return reply_error(INTERNAL_ERROR);
    }

    if (reply_success() < 0) {
        PRINTF("Error: failed to send\n");
        return -1;
    }

    G_swap_ctx.state = PROVIDER_SET;

    return 0;
}
