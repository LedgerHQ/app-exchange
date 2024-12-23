#include <os.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>

#include "globals.h"
#include "trusted_name_descriptor_handler.h"
#include "get_challenge_handler.h"
#include "io_helpers.h"

#include "os_pki.h"
#include "pki.h"
#include "cx.h"
#include "tlv.h"
#include "tlv_utils.h"
#include "macros.h"

#define TYPE_ADDRESS      0x06
#define TYPE_DYN_RESOLVER 0x06

#define STRUCT_TYPE_TRUSTED_NAME 0x03
#define ALGO_SECP256K1           1

#define KEY_ID_TEST 0x00
#define KEY_ID_PROD 0x07

// Reuse the size of the protobuf structure (-1 because TLV data is not NULL terminated)
#define MAX_ADDRESS_LENGTH (sizeof(G_swap_ctx.swap_transaction.payout_address) - 1)

static bool handle_struct_type(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_uint8_t_from_tlv_data(data, &trusted_name_info->struct_type);
}

static bool handle_struct_version(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_uint8_t_from_tlv_data(data, &trusted_name_info->struct_version);
}

static bool handle_challenge(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_uint32_from_tlv_data(data, &trusted_name_info->challenge);
}

static bool handle_sign_key_id(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_uint8_t_from_tlv_data(data, &trusted_name_info->key_id);
}

static bool handle_sign_algo(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_uint8_t_from_tlv_data(data, &trusted_name_info->sig_algorithm);
}

static bool handle_signature(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_cbuf_from_tlv_data(data, &trusted_name_info->input_sig, 1, 0);
}

static bool handle_trusted_name(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_cbuf_from_tlv_data(data, &trusted_name_info->trusted_name, 1, MAX_ADDRESS_LENGTH);
}

static bool handle_address(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_cbuf_from_tlv_data(data, &trusted_name_info->owner, 1, MAX_ADDRESS_LENGTH);
}

static bool handle_trusted_name_type(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_uint8_t_from_tlv_data(data, &trusted_name_info->name_type);
}

static bool handle_trusted_name_source(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    return get_uint8_t_from_tlv_data(data, &trusted_name_info->name_source);
}

static bool handle_chain_id(const tlv_data_t *data, tlv_out_t *trusted_name_info) {
    switch (data->length) {
        case 1:
            trusted_name_info->chain_id = data->value[0];
            return true;
        case 2:
            trusted_name_info->chain_id = (data->value[0] << 8) | data->value[1];
            return true;
        default:
            PRINTF("Error while parsing chain ID: length = %d\n", data->length);
            return false;
    }
}

/**
 * Verify the validity of the received trusted struct
 *
 * @param[in] trusted_name_info the trusted name information
 * @return whether the struct is valid
 */
static swap_error_e verify_struct(const tlv_out_t *trusted_name_info,
                                  uint32_t received_tags_flags) {
    if (!(get_tag_flag(STRUCT_TYPE) & received_tags_flags)) {
        PRINTF("Error: no struct type specified!\n");
        return MISSING_TLV_CONTENT;
    }
    if (!(get_tag_flag(STRUCT_VERSION) & received_tags_flags)) {
        PRINTF("Error: no struct version specified!\n");
        return MISSING_TLV_CONTENT;
    }

    uint32_t expected_challenge = get_challenge();

#ifdef TRUSTED_NAME_TEST_KEY
    uint8_t valid_key_id = KEY_ID_TEST;
#else
    uint8_t valid_key_id = KEY_ID_PROD;
#endif

    switch (trusted_name_info->struct_version) {
        case 2:
            if (!RECEIVED_REQUIRED_TAGS(received_tags_flags,
                                        STRUCT_TYPE,
                                        STRUCT_VERSION,
                                        TRUSTED_NAME_TYPE,
                                        TRUSTED_NAME_SOURCE,
                                        TRUSTED_NAME,
                                        CHAIN_ID,
                                        ADDRESS,
                                        CHALLENGE,
                                        SIGNER_KEY_ID,
                                        SIGNER_ALGO,
                                        SIGNATURE)) {
                PRINTF("Error: missing required fields in struct version 2\n");
                return MISSING_TLV_CONTENT;
            }
            if (trusted_name_info->challenge != expected_challenge) {
                // No risk printing it as DEBUG cannot be used in prod
                PRINTF("Error: wrong challenge, received %u expected %u\n",
                       trusted_name_info->challenge,
                       expected_challenge);
                return WRONG_CHALLENGE;
            }
            if (trusted_name_info->struct_type != STRUCT_TYPE_TRUSTED_NAME) {
                PRINTF("Error: unexpected struct type %d\n", trusted_name_info->struct_type);
                return WRONG_TLV_CONTENT;
            }
            if (trusted_name_info->name_type != TYPE_ADDRESS) {
                PRINTF("Error: unsupported name type %d\n", trusted_name_info->name_type);
                return WRONG_TLV_CONTENT;
            }
            if (trusted_name_info->name_source != TYPE_DYN_RESOLVER) {
                PRINTF("Error: unsupported name source %d\n", trusted_name_info->name_source);
                return WRONG_TLV_CONTENT;
            }
            if (trusted_name_info->sig_algorithm != ALGO_SECP256K1) {
                PRINTF("Error: unsupported sig algorithm %d\n", trusted_name_info->sig_algorithm);
                return WRONG_TLV_CONTENT;
            }
            if (trusted_name_info->key_id != valid_key_id) {
                PRINTF("Error: wrong metadata key ID %u\n", trusted_name_info->key_id);
                return WRONG_TLV_KEY_ID;
            }
            break;
        default:
            PRINTF("Error: unsupported struct version %d\n", trusted_name_info->struct_version);
            return WRONG_TLV_CONTENT;
    }
    return SUCCESS;
}

static bool apply_trusted_name(char *current_address,
                               size_t current_address_size,
                               const cbuf_t *trusted_name,
                               const cbuf_t *owner) {
    uint8_t current_length = strlen(current_address);
    if (trusted_name->size == current_length) {
        PRINTF("Checking against current address %.*H\n", current_length, current_address);
        if (memcmp(trusted_name->bytes, current_address, current_length) == 0) {
            PRINTF("Current address matches, replacing it\n");
            if (owner->size < current_address_size) {
                explicit_bzero(current_address, current_address_size);
                memcpy(current_address, owner->bytes, owner->size);
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
    swap_error_e ret;

    // Main structure that will received the parsed TLV data
    tlv_out_t trusted_name_info;
    memset(&trusted_name_info, 0, sizeof(trusted_name_info));

    // Will be filled by the parser with the flags of received tags
    uint32_t received_tags_flags = 0;

    // The parser will fill it with the hash of the whole TLV payload (except SIGN tag)
    uint8_t tlv_hash[INT256_LENGTH] = {0};

    // Mapping of tags to handler functions. Given ot the parser
    tlv_handler_t handlers[TLV_COUNT] = {
        {.tag = STRUCT_TYPE, .func = &handle_struct_type},
        {.tag = STRUCT_VERSION, .func = &handle_struct_version},
        {.tag = TRUSTED_NAME_TYPE, .func = &handle_trusted_name_type},
        {.tag = TRUSTED_NAME_SOURCE, .func = &handle_trusted_name_source},
        {.tag = TRUSTED_NAME_NFT_ID, .func = NULL},
        {.tag = TRUSTED_NAME, .func = &handle_trusted_name},
        {.tag = CHAIN_ID, .func = &handle_chain_id},
        {.tag = ADDRESS, .func = &handle_address},
        {.tag = SOURCE_CONTRACT, .func = NULL},
        {.tag = CHALLENGE, .func = &handle_challenge},
        {.tag = NOT_VALID_AFTER, .func = NULL},
        {.tag = SIGNER_KEY_ID, .func = &handle_sign_key_id},
        {.tag = SIGNER_ALGO, .func = &handle_sign_algo},
        {.tag = SIGNATURE, .func = &handle_signature},
    };

    // Call the parser to extract the raw TLV payload into our parsed structure
    if (!parse_tlv(handlers,
                   ARRAY_LENGTH(handlers),
                   &cmd->data,
                   &trusted_name_info,
                   SIGNATURE,
                   tlv_hash,
                   &received_tags_flags)) {
        PRINTF("Failed to parse tlv payload\n");
        return reply_error(WRONG_TLV_FORMAT);
    }

    // Verify that the fields received are correct in our context
    ret = verify_struct(&trusted_name_info, received_tags_flags);
    if (ret != SUCCESS) {
        PRINTF("Failed to verify tlv payload\n");
        return reply_error(ret);
    }

    // Verify that the TLV is properly signed using the PKI
    ret = check_signature_with_pki(tlv_hash,
                                   INT256_LENGTH,
                                   CERTIFICATE_PUBLIC_KEY_USAGE_TRUSTED_NAME,
                                   CX_CURVE_SECP256K1,
                                   &trusted_name_info.input_sig);
    if (ret != SUCCESS) {
        PRINTF("Failed to verify signature of trusted name info\n");
        return reply_error(ret);
    }

    PRINTF("trusted_name %.*H owned by %.*H\n",
           trusted_name_info.trusted_name.size,
           trusted_name_info.trusted_name.bytes,
           trusted_name_info.owner.size,
           trusted_name_info.owner.bytes);

    // Should never happen thanks to apdu_parser check but let's check again anyway
    if (G_swap_ctx.subcommand != SWAP && G_swap_ctx.subcommand != SWAP_NG) {
        PRINTF("Trusted name descriptor is only for SWAP based flows\n");
        return reply_error(INTERNAL_ERROR);
    }

    PRINTF("Checking against PAYOUT address %.*H\n",
           sizeof(G_swap_ctx.swap_transaction.payout_address),
           G_swap_ctx.swap_transaction.payout_address);
    apply_trusted_name(G_swap_ctx.swap_transaction.payout_address,
                       sizeof(G_swap_ctx.swap_transaction.payout_address),
                       &trusted_name_info.trusted_name,
                       &trusted_name_info.owner);

    PRINTF("Checking against REFUND address %.*H\n",
           sizeof(G_swap_ctx.swap_transaction.refund_address),
           G_swap_ctx.swap_transaction.refund_address);
    apply_trusted_name(G_swap_ctx.swap_transaction.refund_address,
                       sizeof(G_swap_ctx.swap_transaction.refund_address),
                       &trusted_name_info.trusted_name,
                       &trusted_name_info.owner);

    return reply_success();
}

// Wrapper around trusted_name_descriptor_handler_internal to handle the challenge reroll
int trusted_name_descriptor_handler(const command_t *cmd) {
    int ret = trusted_name_descriptor_handler_internal(cmd);
    // prevent brute-force guesses
    roll_challenge();
    return ret;
}
