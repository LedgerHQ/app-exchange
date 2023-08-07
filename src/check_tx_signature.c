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
#define R_S_INT_SIZE 32
#define DER_HEADER_SIZE 2
#define DER_OFFSET_LENGTH 1

// This function receive transaction signature
// Input should be in the form of DER serialized signature
// the length should be CURVE_SIZE_BYTES * 2 + 6 (DER encoding)
int check_tx_signature(const command_t *cmd) {
    // If we received the data in (R,S) format we will encode it here in DER before veryfing the signature
    uint8_t der_sig[DER_HEADER_SIZE + MAX_DER_INT_SIZE(R_S_INT_SIZE) * 2];
    buf_t signature;

    if (cmd->subcommand == SWAP || cmd->subcommand == FUND) {
        // We received the signature in DER format, just perform some sanity checks
        if (cmd->data.size < MIN_DER_SIGNATURE_LENGTH || cmd->data.size > MAX_DER_SIGNATURE_LENGTH) {
            PRINTF("Error: Input buffer length don't correspond to DER length\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }

        uint16_t payload_size = cmd->data.bytes[DER_OFFSET_LENGTH];
        if (payload_size + DER_HEADER_SIZE != cmd->data.size) {
            PRINTF("DER signature header advertizes %d bytes, we received %d\n", payload_size, cmd->data.size);
            return reply_error(INCORRECT_COMMAND_DATA);
        }
        signature = cmd->data;
    } else {
        // We received the signature in (R,S) format, perform some sanity checks then encode in DER
        if (cmd->data.size != R_S_INT_SIZE * 2) {
            PRINTF("Error: Input buffer length don't correspond to (R, S) length\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }

        uint8_t *r = cmd->data.bytes;
        uint8_t *s = cmd->data.bytes + R_S_INT_SIZE;
        size_t der_r_len = asn1_get_encoded_integer_size(r, R_S_INT_SIZE);
        size_t der_s_len = asn1_get_encoded_integer_size(s, R_S_INT_SIZE);
        size_t size = der_r_len + der_s_len + DER_HEADER_SIZE;

        // First check the size to ensure it fits and we can cast down
        if (size > sizeof(der_sig)) {
            PRINTF("Error: Unexpected der integer size\n");
            return reply_error(SIGN_VERIFICATION_FAIL);
        }

        encode_sig_der(der_sig, size, r, R_S_INT_SIZE, s, R_S_INT_SIZE);

        signature.size = size;
        signature.bytes = der_sig;
    }

    PRINTF("DER sig: %.*H\n", signature.size, signature.bytes);
    PRINTF("SHA256(payload): %.*H\n", sizeof(G_swap_ctx.sha256_digest), G_swap_ctx.sha256_digest);

    // Check the signature of the sha256_digest we computed from the tx payload
    if (cx_ecdsa_verify(&G_swap_ctx.partner.public_key,
                        CX_LAST,
                        CX_SHA256,
                        G_swap_ctx.sha256_digest,
                        CURVE_SIZE_BYTES,
                        signature.bytes,
                        signature.size) == 0) {
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
