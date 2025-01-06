#include <os.h>
#include <cx.h>

#include "globals.h"
#include "set_partner_key.h"
#include "swap_errors.h"
#include "globals.h"
#include "buffer.h"
#include "io_helpers.h"
#include "cx.h"

static uint16_t parse_set_partner_key_command(const command_t *cmd,
                                              buf_t *partner_name,
                                              uint8_t **raw_pubkey,
                                              cx_curve_t *curve) {
    // data is serialized as
    // 1 byte - partner name length L
    // L bytes - partner name
    // 1 byte - curve used / NG FLOWS ONLY
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

    // On Legacy flows, the curve used depends of the flow
    // On NG flows, it is specified in the APDU
    if (cmd->subcommand == SWAP) {
        *curve = CX_CURVE_SECP256K1;
    } else if (cmd->subcommand == SELL || cmd->subcommand == FUND) {
        *curve = CX_CURVE_256R1;
    } else {
        uint8_t curve_id;
        if (!pop_uint8_from_buffer(cmd->data.bytes, cmd->data.size, &curve_id, &offset)) {
            PRINTF("Failed to read curve ID\n");
            return INCORRECT_COMMAND_DATA;
        }
        if (curve_id == CURVE_SECP256K1) {
            *curve = CX_CURVE_SECP256K1;
        } else if (curve_id == CURVE_SECP256R1) {
            *curve = CX_CURVE_256R1;
        } else {
            PRINTF("Error: Incorrect curve specifier %d\n", curve_id);
            return INCORRECT_COMMAND_DATA;
        }
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
    cx_curve_t curve;
    uint16_t err = parse_set_partner_key_command(cmd, &partner, &raw_pubkey, &curve);
    if (err != 0) {
        return reply_error(err);
    }

    if (G_swap_ctx->subcommand == FUND || G_swap_ctx->subcommand == FUND_NG) {
        // Prepare the prefix for FUND display
        memset(G_swap_ctx->partner.prefixed_name, 0, sizeof(G_swap_ctx->partner.prefixed_name));
        strlcpy(G_swap_ctx->partner.prefixed_name,
                PARTNER_NAME_PREFIX_FOR_FUND,
                sizeof(G_swap_ctx->partner.prefixed_name));
        // The incoming partner name is NOT NULL terminated, so we use strncat
        // Don't erase the prefix copied above
        strncat(G_swap_ctx->partner.prefixed_name, (char *) partner.bytes, partner.size);
    } else {
        memset(G_swap_ctx->partner.unprefixed_name, 0, sizeof(G_swap_ctx->partner.unprefixed_name));
        // The incoming partner name is NOT NULL terminated, so we use strncpy
        strncpy(G_swap_ctx->partner.unprefixed_name, (char *) partner.bytes, partner.size);
    }

    // Create the verifying key from the raw public key
    if (cx_ecfp_init_public_key_no_throw(curve,
                                         raw_pubkey,
                                         UNCOMPRESSED_KEY_LENGTH,
                                         &(G_swap_ctx->partner.public_key)) != CX_OK) {
        PRINTF("Error: cx_ecfp_init_public_key_no_throw\n");
        return reply_error(INTERNAL_ERROR);
    }

    // Save the hash of the entire credentials to check that the Ledger key signed it later
    if (cx_hash_sha256(cmd->data.bytes,
                       cmd->data.size,
                       G_swap_ctx->sha256_digest_no_prefix,
                       sizeof(G_swap_ctx->sha256_digest_no_prefix)) == 0) {
        PRINTF("cx_hash_sha256 internal error\n");
        return reply_error(INTERNAL_ERROR);
    }

    if (reply_success() < 0) {
        PRINTF("Error: failed to send\n");
        return -1;
    }

    G_swap_ctx->state = PROVIDER_SET;

    return 0;
}
