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

typedef int (*StateCommandDispatcher)(subcommand_e subcommand,           //
                                      swap_app_context_t *ctx,           //
                                      unsigned char *input_buffer,       //
                                      unsigned int input_buffer_length,  //
                                      SendFunction send);

// clang-format off
static const StateCommandDispatcher dispatcher_table[COMMAND_UPPER_BOUND-2][STATE_UPPER_BOUND] = {
//                                               INITIAL_STATE          WAITING_TRANSACTION     PROVIDER_SET            PROVIDER_CHECKED,       TRANSACTION_RECIEVED    SIGNATURE_CHECKED       TO_ADDR_CHECKED         WAITING_USER_VALIDATION     WAITING_SIGNING
/* GET_VERSION_COMMAND                      */  {get_version_handler,   get_version_handler,    get_version_handler,    get_version_handler,    get_version_handler,    get_version_handler,    get_version_handler,    unexpected_command,         unexpected_command},
/* START_NEW_TRANSACTION_COMMAND            */  {start_new_transaction, start_new_transaction,  start_new_transaction,  start_new_transaction,  start_new_transaction,  start_new_transaction,  start_new_transaction,  unexpected_command,         start_new_transaction},
/* SET_PARTNER_KEY_COMMAND                  */  {unexpected_command,    set_partner_key,        unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,         unexpected_command},
/* CHECK_PARTNER                            */  {unexpected_command,    unexpected_command,     check_partner,          unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,         unexpected_command},
/* PROCESS_TRANSACTION_COMMAND              */  {unexpected_command,    unexpected_command,     unexpected_command,     process_transaction,    unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,         unexpected_command},
/* CHECK_TRANSACTION_SIGNATURE_COMMAND      */  {unexpected_command,    unexpected_command,     unexpected_command,     unexpected_command,     check_tx_signature,     unexpected_command,     unexpected_command,     unexpected_command,         unexpected_command},
/* CHECK_TO_ADDRESS                         */  {unexpected_command,    unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     check_payout_address,   unexpected_command,     unexpected_command,         unexpected_command},
/* CHECK_REFUND_ADDRESS                     */  {unexpected_command,    unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     check_refund_address,   unexpected_command,         unexpected_command},
/* START_SIGNING_TRANSACTION                */  {unexpected_command,    unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,         start_signing_transaction}
};
// clang-format on

int dispatch_command(command_e command, subcommand_e subcommand,             //
                     swap_app_context_t *context,                            //
                     unsigned char *input_buffer, unsigned int buffer_size,  //
                     SendFunction send) {
    StateCommandDispatcher handler;

    PRINTF("command: %d, subcommand: %d, state: %d\n", command, subcommand, context->state);

    if (subcommand >= SUBCOMMAND_UPPER_BOUND) {
        return reply_error(context, WRONG_P2, send);
    }

    // CHECK_ASSET_IN command instead of CHECK_TO_ADDRESS.
    if (subcommand == SELL && command == CHECK_PAYOUT_ADDRESS) {
        handler = (StateCommandDispatcher)(PIC(check_asset_in));
    } else {
        handler = (StateCommandDispatcher)(PIC(dispatcher_table[command - 2][context->state]));
    }

    return handler(subcommand, context, input_buffer, buffer_size, send);
}
