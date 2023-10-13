#include <os.h>
#include <cx.h>

#include "check_tx_signature.h"
#include "globals.h"
#include "swap_errors.h"
#include "io.h"
#include "der.h"

// One int (r or s) in DER is (1 byte prefix + 1 byte r/s length + r/s + 1 optional ending byte)
// Keep the legacy additional '+2' just in case, it has no side effect.
#define MAX_DER_INT_SIZE(size) (1 + 1 + (size) + 1 + 2)
#define R_S_INT_SIZE           32
#define DER_HEADER_SIZE        2
#define DER_OFFSET_LENGTH      1

// This function receive transaction signature
// Input should be in the form of DER serialized signature
// the length should be CURVE_SIZE_BYTES * 2 + 6 (DER encoding)
int check_tx_signature(const command_t *cmd) {
    // If we received the data in (R,S) format we will encode it here in DER before veryfing the
    // signature
    uint8_t der_sig[DER_HEADER_SIZE + MAX_DER_INT_SIZE(R_S_INT_SIZE) * 2];
    buf_t signature;
    bool signature_is_in_R_S_format;
    bool signature_is_computed_on_dot_prefixed_tx;
    uint16_t offset = 0;

    if (cmd->subcommand == SWAP) {
        signature_is_in_R_S_format = false;
        signature_is_computed_on_dot_prefixed_tx = false;
    } else if (cmd->subcommand == FUND) {
        signature_is_in_R_S_format = false;
        signature_is_computed_on_dot_prefixed_tx = true;
    } else if (cmd->subcommand == SELL) {
        signature_is_in_R_S_format = true;
        signature_is_computed_on_dot_prefixed_tx = true;
    } else {
        uint8_t dot_prefixed_tx;
        if (!pop_uint8_from_buffer(cmd->data.bytes, cmd->data.size, &dot_prefixed_tx, &offset)) {
            PRINTF("Failed to read prefix selector\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }
        if (dot_prefixed_tx == SIGNATURE_COMPUTED_ON_TX) {
            signature_is_computed_on_dot_prefixed_tx = false;
        } else if (dot_prefixed_tx == SIGNATURE_COMPUTED_ON_DOT_PREFIXED_TX) {
            signature_is_computed_on_dot_prefixed_tx = true;
        } else {
            PRINTF("Error: Incorrect prefix selector %d\n", dot_prefixed_tx);
            return reply_error(INCORRECT_COMMAND_DATA);
        }

        uint8_t sig_format;
        if (!pop_uint8_from_buffer(cmd->data.bytes, cmd->data.size, &sig_format, &offset)) {
            PRINTF("Failed to read signature format selector\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }
        if (sig_format == DER_FORMAT_SIGNATURE) {
            signature_is_in_R_S_format = false;
        } else if (sig_format == R_S_FORMAT_SIGNATURE) {
            signature_is_in_R_S_format = true;
        } else {
            PRINTF("Error: Incorrect signature format selector %d\n", sig_format);
            return reply_error(INCORRECT_COMMAND_DATA);
        }
    }

    buf_t remaining_input;
    remaining_input.size = cmd->data.size - offset;
    remaining_input.bytes = cmd->data.bytes + offset;
    if (!signature_is_in_R_S_format) {
        // We received the signature in DER format, just perform some sanity checks
        if (remaining_input.size < MIN_DER_SIGNATURE_LENGTH ||
            remaining_input.size > MAX_DER_SIGNATURE_LENGTH) {
            PRINTF("Error: Input buffer length don't correspond to DER length\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }

        uint16_t payload_size = remaining_input.bytes[DER_OFFSET_LENGTH];
        if (payload_size + DER_HEADER_SIZE != remaining_input.size) {
            PRINTF("DER signature header advertizes %d bytes, we received %d\n",
                   payload_size,
                   remaining_input.size);
            return reply_error(INCORRECT_COMMAND_DATA);
        }
        signature.size = remaining_input.size;
        signature.bytes = remaining_input.bytes;
    } else {
        // We received the signature in (R,S) format, perform some sanity checks then encode in DER
        if (remaining_input.size != R_S_INT_SIZE * 2) {
            PRINTF("Error: Input buffer length don't correspond to (R, S) length\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }

        uint8_t *r = remaining_input.bytes;
        uint8_t *s = remaining_input.bytes + R_S_INT_SIZE;
        size_t der_r_len = asn1_get_encoded_integer_size(r, R_S_INT_SIZE);
        size_t der_s_len = asn1_get_encoded_integer_size(s, R_S_INT_SIZE);
        size_t size = der_r_len + der_s_len + DER_HEADER_SIZE;

        // First check the size to ensure it fits and we can cast down
        if (size > sizeof(der_sig)) {
            PRINTF("Error: Unexpected der integer size\n");
            return reply_error(SIGN_VERIFICATION_FAIL);
        }

        if (encode_sig_der(der_sig, size, r, R_S_INT_SIZE, s, R_S_INT_SIZE) == 0) {
            PRINTF("Error: Failed to encode DER signature\n");
            return reply_error(SIGN_VERIFICATION_FAIL);
        }

        signature.size = size;
        signature.bytes = der_sig;
    }

    PRINTF("DER sig: %.*H\n", signature.size, signature.bytes);
    const uint8_t *hash;
    if (signature_is_computed_on_dot_prefixed_tx) {
        hash = G_swap_ctx.sha256_digest_prefixed;
        PRINTF("SHA256 %.*H\n",
               sizeof(G_swap_ctx.sha256_digest_prefixed),
               G_swap_ctx.sha256_digest_prefixed);
    } else {
        hash = G_swap_ctx.sha256_digest_no_prefix;
        PRINTF("SHA256 %.*H\n",
               sizeof(G_swap_ctx.sha256_digest_no_prefix),
               G_swap_ctx.sha256_digest_no_prefix);
    }

    // Check the signature of the sha256_digest we computed from the tx payload
    if (!cx_ecdsa_verify_no_throw(&G_swap_ctx.partner.public_key,
                                  hash,
                                  CURVE_SIZE_BYTES,
                                  signature.bytes,
                                  signature.size)) {
        PRINTF("Error: Failed to verify signature of received transaction\n");
        return reply_error(SIGN_VERIFICATION_FAIL);
    }

    if (reply_success() < 0) {
        PRINTF("Error: Can't send message\n");
        return -1;
    }

    G_swap_ctx.state = SIGNATURE_CHECKED;

    return 0;
}
