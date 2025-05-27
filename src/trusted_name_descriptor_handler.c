#include <os.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>

#include "globals.h"
#include "trusted_name_descriptor_handler.h"
#include "tlv_use_case_trusted_name.h"
#include "get_challenge_handler.h"
#include "io_helpers.h"

#include "cx.h"
#include "io.h"
#include "macros.h"

static bool apply_trusted_name(char *current_address,
                               size_t current_address_size,
                               const buffer_t *trusted_name,
                               const buffer_t *owner) {
    uint8_t current_length = strlen(current_address);
    if (trusted_name->size == current_length) {
        PRINTF("Checking against current address %.*H\n", current_length, current_address);
        if (memcmp(trusted_name->ptr, current_address, current_length) == 0) {
            PRINTF("Current address matches, replacing it\n");
            if (owner->size < current_address_size) {
                explicit_bzero(current_address, current_address_size);
                memcpy(current_address, owner->ptr, owner->size);
                return true;
            } else {
                // Should never happen thanks to the parser but let's double check
                PRINTF("Error, owner address does not fit\n");
            }
        }
    }
    return false;
}

static int trusted_name_descriptor_handler_internal(const command_t *cmd) {
    PRINTF("Received chunk of trusted info, length = %d\n", cmd->data.size);
    PRINTF("Content = %.*H\n", cmd->data.size, cmd->data.bytes);

    // Should never happen thanks to apdu_parser check but let's check again anyway
    if (G_swap_ctx.subcommand != SWAP && G_swap_ctx.subcommand != SWAP_NG) {
        PRINTF("Trusted name descriptor is only for SWAP based flows\n");
        return reply_error(INTERNAL_ERROR);
    }

    tlv_trusted_name_out_t tlv_output = {0};

    buffer_t payload = {.ptr = cmd->data.bytes, .size = cmd->data.size};

    tlv_trusted_name_status_t err = tlv_use_case_trusted_name(&payload, &tlv_output);
    if (err != TLV_TRUSTED_NAME_SUCCESS) {
        PRINTF("tlv_use_case_parse_trusted_name_payload failed\n");
        buffer_t error_context = {.ptr = &err, .size = sizeof(err)};
        return io_send_response_buffer(&error_context, WRONG_TRUSTED_NAME_TLV);
    }

    // Check Exchange specific required tags
    if (!tlv_output.challenge_received) {
        PRINTF("Error: missing Exchange required fields\n");
        return reply_error(MISSING_TLV_CONTENT);
    }

    uint32_t expected_challenge = get_challenge();
    if (tlv_output.challenge != expected_challenge) {
        PRINTF("Error: wrong challenge, received %u expected %u\n",
               tlv_output.challenge,
               expected_challenge);
        return reply_error(WRONG_TLV_CHALLENGE);
    }

    if (tlv_output.trusted_name_type != TLV_TRUSTED_NAME_TYPE_CONTEXT_ADDRESS) {
        PRINTF("Error: unsupported name type %d\n", tlv_output.trusted_name_type);
        return reply_error(WRONG_TLV_CONTENT);
    }

    if (tlv_output.trusted_name_source != TLV_TRUSTED_NAME_SOURCE_DYNAMIC_RESOLVER) {
        PRINTF("Error: unsupported name source %d\n", tlv_output.trusted_name_source);
        return reply_error(WRONG_TLV_CONTENT);
    }

    PRINTF("trusted_name %.*H owned by %.*H\n",
           tlv_output.trusted_name.size,
           tlv_output.trusted_name.ptr,
           tlv_output.address.size,
           tlv_output.address.ptr);

    bool applied = false;
    PRINTF("Checking against PAYOUT address %.*H\n",
           sizeof(G_swap_ctx.swap_transaction.payout_address),
           G_swap_ctx.swap_transaction.payout_address);
    applied |= apply_trusted_name(G_swap_ctx.swap_transaction.payout_address,
                                  sizeof(G_swap_ctx.swap_transaction.payout_address),
                                  &tlv_output.trusted_name,
                                  &tlv_output.address);

    PRINTF("Checking against REFUND address %.*H\n",
           sizeof(G_swap_ctx.swap_transaction.refund_address),
           G_swap_ctx.swap_transaction.refund_address);
    applied |= apply_trusted_name(G_swap_ctx.swap_transaction.refund_address,
                                  sizeof(G_swap_ctx.swap_transaction.refund_address),
                                  &tlv_output.trusted_name,
                                  &tlv_output.address);

    if (!applied) {
        PRINTF("Error: descriptor has not been applied on either REFUND nor PAYOUT addresses\n");
        return reply_error(DESCRIPTOR_NOT_USED);
    }

    return reply_success();
}

// Wrapper around trusted_name_descriptor_handler_internal to handle the challenge reroll
int trusted_name_descriptor_handler(const command_t *cmd) {
    int ret = trusted_name_descriptor_handler_internal(cmd);
    // prevent brute-force guesses
    roll_challenge();
    return ret;
}
