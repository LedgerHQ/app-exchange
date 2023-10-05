#include <cx.h>
#include <os.h>

#include "check_partner.h"
#include "globals.h"
#include "swap_errors.h"
#include "io.h"

// This function receive signature of
// Input should be in the form of DER serialized signature
// the length should be in [MIN_DER_SIGNATURE_LENGTH, MAX_DER_SIGNATURE_LENGTH]
int check_partner(const command_t *cmd) {
    if (cmd->data.size < MIN_DER_SIGNATURE_LENGTH || cmd->data.size > MAX_DER_SIGNATURE_LENGTH) {
        PRINTF("Error: Input buffer length don't correspond to DER length\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    if (!cx_ecdsa_verify_no_throw(&(G_swap_ctx.ledger_public_key),
                                  G_swap_ctx.sha256_digest,
                                  CURVE_SIZE_BYTES,
                                  cmd->data.bytes,
                                  cmd->data.size)) {
        PRINTF("Error: Failed to verify signature of partner data\n");
        return reply_error(SIGN_VERIFICATION_FAIL);
    }

    if (reply_success() < 0) {
        PRINTF("Error: send error\n");
        return -1;
    }

    G_swap_ctx.state = PROVIDER_CHECKED;

    return 0;
}
