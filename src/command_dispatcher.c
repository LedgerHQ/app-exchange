#include "command_dispatcher.h"
#include "os.h"

#include "globals.h"
#include "get_version_handler.h"
#include "start_new_transaction.h"
#include "set_partner_key.h"
#include "process_transaction.h"
#include "check_tx_signature.h"
#include "apdu_offsets.h"
#include "check_partner.h"
#include "start_signing_transaction.h"
#include "check_addresses_and_amounts.h"
#include "prompt_ui_display.h"
#include "get_challenge_handler.h"
#include "trusted_name_descriptor_handler.h"

#include "io.h"

int dispatch_command(const command_t *cmd) {
    PRINTF("command: %d, subcommand: %d, current state: %d\n",
           cmd->ins,
           cmd->subcommand,
           G_swap_ctx.state);

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
        case GET_CHALLENGE:
            ret = get_challenge_handler();
            break;
        case SEND_TRUSTED_NAME_DESCRIPTOR:
            ret = trusted_name_descriptor_handler(cmd);
            break;
        case CHECK_PAYOUT_ADDRESS:
        case CHECK_ASSET_IN_AND_DISPLAY:
        case CHECK_ASSET_IN_NO_DISPLAY:
        case CHECK_REFUND_ADDRESS_AND_DISPLAY:
        case CHECK_REFUND_ADDRESS_NO_DISPLAY:
            ret = check_addresses_and_amounts(cmd);
            break;
        case PROMPT_UI_DISPLAY:
            ret = prompt_ui_display(cmd);
            break;
        case START_SIGNING_TRANSACTION:
            ret = start_signing_transaction(cmd);
            break;
        default:
            __builtin_trap();
            break;
    }

    return ret;
}
