#include <os.h>
#include <cx.h>

#include "check_tx_signature.h"
#include "globals.h"
#include "swap_errors.h"
#include "io.h"
#include "der.h"

#define MAX_DER_INT_SIZE(size) (1 + 3 + (size) + 1)

// This function receive transaction signature
// Input should be in the form of DER serialized signature
// the length should be CURVE_SIZE_BYTES * 2 + 6 (DER encoding)
int check_tx_signature(const command_t *cmd) {
    if (cmd->subcommand == SWAP || cmd->subcommand == FUND) {
        if (cmd->data.size < MIN_DER_SIGNATURE_LENGTH ||
            cmd->data.size > MAX_DER_SIGNATURE_LENGTH || cmd->data.bytes[1] + 2 != cmd->data.size) {
            PRINTF("Error: Input buffer length don't correspond to DER length\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }
        if (cx_ecdsa_verify(&G_swap_ctx.partner.public_key,
                            CX_LAST,
                            CX_SHA256,
                            G_swap_ctx.sha256_digest,
                            CURVE_SIZE_BYTES,
                            cmd->data.bytes,
                            cmd->data.size) == 0) {
            PRINTF("Error: Failed to verify signature of received transaction\n");
            return reply_error(SIGN_VERIFICATION_FAIL);
        }
    } else if (cmd->subcommand == SELL || cmd->subcommand == SWAP_NG || cmd->subcommand == FUND_NG || cmd->subcommand == SELL_NG) {
        if (cmd->data.size != 64) {
            PRINTF("Error: Input buffer length don't correspond to (R, S) length\n");
            return reply_error(INCORRECT_COMMAND_DATA);
        }

        size_t der_r_len = asn1_get_encoded_integer_size(cmd->data.bytes, 32);
        size_t der_s_len = asn1_get_encoded_integer_size(cmd->data.bytes + 32, 32);
        size_t size = der_r_len + der_s_len + 2;

        unsigned char der_sig[MAX_DER_INT_SIZE(32) * 2 + 2];
        if (size > sizeof(der_sig)) {
            PRINTF("Error: Unexpected der integer size\n");
            return reply_error(SIGN_VERIFICATION_FAIL);
        }

        encode_sig_der(der_sig, size, cmd->data.bytes, 32, cmd->data.bytes + 32, 32);

        PRINTF("DER sig: %.*H\n", size, der_sig);
        PRINTF("SHA256(payload): %.*H\n",
               sizeof(G_swap_ctx.sha256_digest),
               G_swap_ctx.sha256_digest);

        if (cx_ecdsa_verify(&G_swap_ctx.partner.public_key,
                            CX_LAST,
                            CX_SHA256,
                            G_swap_ctx.sha256_digest,
                            CURVE_SIZE_BYTES,
                            der_sig,
                            size) == 0) {
            PRINTF("Error: Failed to verify signature of received transaction\n");
            return reply_error(SIGN_VERIFICATION_FAIL);
        }
    } else {
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    if (reply_success() < 0) {
        PRINTF("Error: Can't send message\n");
        return -1;
    }

    G_swap_ctx.state = SIGNATURE_CHECKED;

    return 0;
}
