#include "command_dispatcher.h"
#include "os.h"

#include "globals.h"
#include "get_version_handler.h"
#include "start_new_transaction.h"
#include "set_partner_key.h"
#include "process_transaction.h"
#include "check_tx_signature.h"
#include "check_payout_address.h"
#include "check_refund_address.h"
#include "check_asset_in.h"
#include "apdu_offsets.h"
#include "check_partner.h"
#include "start_signing_transaction.h"

#include "io.h"

int dispatch_command(const command_t *cmd) {
    PRINTF("command: %d, subcommand: %d, current state: %d\n", cmd->ins, cmd->subcommand, G_swap_ctx.state);

    int ret = -1;

    switch (cmd->ins) {
        case GET_VERSION_COMMAND:
            ret = get_version_handler();
            break;
        case START_NEW_TRANSACTION_COMMAND:
            ret = start_new_transaction(cmd);
            break;
        case SET_PARTNER_KEY_COMMAND:
            ret = set_partner_key(cmd);
            break;
        case CHECK_PARTNER_COMMAND:
            ret = check_partner(cmd);
            break;
        case PROCESS_TRANSACTION_RESPONSE_COMMAND:
            ret = process_transaction(cmd);
            break;
        case CHECK_TRANSACTION_SIGNATURE_COMMAND:
            ret = check_tx_signature(cmd);
            break;
        case CHECK_PAYOUT_ADDRESS:
            if (cmd->subcommand == SELL || cmd->subcommand == FUND || cmd->subcommand == SELL_NG || cmd->subcommand == FUND_NG) {
                ret = check_asset_in(cmd);
            } else {
                ret = check_payout_address(cmd);
            }
            break;
        case CHECK_REFUND_ADDRESS:
            ret = check_refund_address(cmd);
            break;
        case START_SIGNING_TRANSACTION:
            ret = start_signing_transaction(cmd);
            break;
        default:
            __builtin_unreachable();
            break;
    }

    return ret;
}
