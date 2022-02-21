#include "command_dispatcher.h"
#include "os.h"

#include "swap_app_context.h"
#include "get_version_handler.h"
#include "unexpected_command.h"
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

#include "reply_error.h"

typedef int (*StateCommandDispatcher)(swap_app_context_t *ctx,
                                      const command_t *cmd,
                                      SendFunction send);

int dispatch_command(swap_app_context_t *context, const command_t *cmd, SendFunction send) {
    StateCommandDispatcher handler;

    PRINTF("command: %d, subcommand: %d, state: %d\n", cmd->ins, cmd->subcommand, context->state);

    if (cmd->rate != FIXED && cmd->rate != FLOATING) {
        return reply_error(context, WRONG_P1, send);
    }
    if (cmd->subcommand != SWAP && cmd->subcommand != SELL && cmd->subcommand != FUND) {
        return reply_error(context, WRONG_P2, send);
    }

    handler = (void *) PIC(unexpected_command);

    switch (cmd->ins) {
        case GET_VERSION_COMMAND:
            if (context->state != WAITING_USER_VALIDATION && context->state != WAITING_SIGNING) {
                handler = (void *) PIC(get_version_handler);
            }
            break;
        case START_NEW_TRANSACTION_COMMAND:
            if (context->state != WAITING_USER_VALIDATION) {
                handler = (void *) PIC(start_new_transaction);
            }
            break;
        case SET_PARTNER_KEY_COMMAND:
            if (context->state == WAITING_TRANSACTION && cmd->subcommand == context->subcommand) {
                handler = (void *) PIC(set_partner_key);
            }
            break;
        case CHECK_PARTNER_COMMAND:
            if (context->state == PROVIDER_SET && cmd->subcommand == context->subcommand) {
                handler = (void *) PIC(check_partner);
            }
            break;
        case PROCESS_TRANSACTION_RESPONSE_COMMAND:
            if (context->state == PROVIDER_CHECKED && cmd->subcommand == context->subcommand) {
                handler = (void *) PIC(process_transaction);
            }
            break;
        case CHECK_TRANSACTION_SIGNATURE_COMMAND:
            if (context->state == TRANSACTION_RECEIVED && cmd->subcommand == context->subcommand) {
                handler = (void *) PIC(check_tx_signature);
            }
            break;
        case CHECK_PAYOUT_ADDRESS:
            if (context->state == SIGNATURE_CHECKED && cmd->subcommand == context->subcommand) {
                if (cmd->subcommand == SELL || cmd->subcommand == FUND) {
                    handler = (void *) PIC(check_asset_in);
                } else {
                    handler = (void *) PIC(check_payout_address);
                }
            }
            break;
        case CHECK_REFUND_ADDRESS:
            if (context->state == TO_ADDR_CHECKED && cmd->subcommand == context->subcommand) {
                handler = (void *) PIC(check_refund_address);
            }
            break;
        case START_SIGNING_TRANSACTION:
            if (context->state == WAITING_SIGNING && cmd->subcommand == context->subcommand) {
                handler = (void *) PIC(start_signing_transaction);
            }
            break;
        default:
            break;
    }

    return handler(context, cmd, send);
}
