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


int dispatch_command(command_t *cmd) {
    PRINTF("command: %d, subcommand: %d, state: %d\n", cmd->ins, cmd->subcommand, G_swap_ctx.state);

    int ret = -1;
    bool valid_command_received = false;

    switch (cmd->ins) {
        case GET_VERSION_COMMAND:
            if (G_swap_ctx.state != WAITING_USER_VALIDATION &&
                G_swap_ctx.state != WAITING_SIGNING) {
                ret = get_version_handler();
                valid_command_received = true;
            }
            break;
        case START_NEW_TRANSACTION_COMMAND:
            if (G_swap_ctx.state != WAITING_USER_VALIDATION) {
                ret = start_new_transaction(cmd);
                valid_command_received = true;
            }
            break;
        case SET_PARTNER_KEY_COMMAND:
            if (G_swap_ctx.state == WAITING_TRANSACTION &&
                cmd->subcommand == G_swap_ctx.subcommand) {
                ret = set_partner_key(cmd);
                valid_command_received = true;
            }
            break;
        case CHECK_PARTNER_COMMAND:
            if (G_swap_ctx.state == PROVIDER_SET && cmd->subcommand == G_swap_ctx.subcommand) {
                ret = check_partner(cmd);
                valid_command_received = true;
            }
            break;
        case PROCESS_TRANSACTION_RESPONSE_COMMAND:
            if (G_swap_ctx.state == PROVIDER_CHECKED && cmd->subcommand == G_swap_ctx.subcommand) {
                ret = process_transaction(cmd);
                valid_command_received = true;
            }
            break;
        case CHECK_TRANSACTION_SIGNATURE_COMMAND:
            if (G_swap_ctx.state == TRANSACTION_RECEIVED &&
                cmd->subcommand == G_swap_ctx.subcommand) {
                ret = check_tx_signature(cmd);
                valid_command_received = true;
            }
            break;
        case CHECK_PAYOUT_ADDRESS:
            if (G_swap_ctx.state == SIGNATURE_CHECKED && cmd->subcommand == G_swap_ctx.subcommand) {
                if (cmd->subcommand == SELL || cmd->subcommand == FUND || cmd->subcommand == SELL_NG || cmd->subcommand == FUND_NG) {
                    ret = check_asset_in(cmd);
                } else {
                    ret = check_payout_address(cmd);
                }
                valid_command_received = true;
            }
            break;
        case CHECK_REFUND_ADDRESS:
            if (G_swap_ctx.state == TO_ADDR_CHECKED && cmd->subcommand == G_swap_ctx.subcommand) {
                ret = check_refund_address(cmd);
                valid_command_received = true;
            }
            break;
        case START_SIGNING_TRANSACTION:
            PRINTF("START_SIGNING_TRANSACTION\n");
            PRINTF("G_swap_ctx.state %d\n", G_swap_ctx.state);
            PRINTF("cmd->subcommand %d\n", cmd->subcommand);
            PRINTF("G_swap_ctx.subcommand %d\n", G_swap_ctx.subcommand);
            if (G_swap_ctx.state == WAITING_SIGNING && cmd->subcommand == G_swap_ctx.subcommand) {
                ret = start_signing_transaction(cmd);
                valid_command_received = true;
            }
            break;
        default:
            break;
    }

    if (!valid_command_received) {
        PRINTF("Invalid command received\n");
        ret = reply_error(INVALID_INSTRUCTION);
    }

    return ret;
}
