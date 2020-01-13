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
#include "apdu_offsets.h"
#include "user_validation.h"

typedef int (*StateCommandDispatcher)(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, SendFunction send);

StateCommandDispatcher dispatcher_table[COMMAND_UPPER_BOUND][STATE_UPPER_BOUND] = {
//                                               INITIAL_STATE          WAITING_TRANSACTION     PROVIDER_SET            TRANSACTION_RECIEVED    SIGNATURE_CHECKED       TO_ADDR_CHECKED         WAITING_USER_VALIDATION
/* GET_VERSION_COMMAND                      */  {get_version_handler,   get_version_handler,    get_version_handler,    get_version_handler,    get_version_handler,    get_version_handler,    unexpected_command},
/* START_NEW_TRANSACTION_COMMAND            */  {start_new_transaction, start_new_transaction,  start_new_transaction,  start_new_transaction,  start_new_transaction,  start_new_transaction,  unexpected_command},
/* SET_PARTNER_KEY_COMMAND                  */  {unexpected_command,    set_partner_key,        unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command},
/* PROCESS_TRANSACTION_COMMAND              */  {unexpected_command,    unexpected_command,     process_transaction,    unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command},
/* CHECK_TRANSACTION_SIGNATURE_COMMAND      */  {unexpected_command,    unexpected_command,     unexpected_command,     check_tx_signature,     unexpected_command,     unexpected_command,     unexpected_command},
/* CHECK_TO_ADDRESS                         */  {unexpected_command,    unexpected_command,     unexpected_command,     unexpected_command,     check_payout_address,   unexpected_command,     unexpected_command},
/* CHECK_REFUND_ADDRESS                     */  {unexpected_command,    unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     check_refund_address,   unexpected_command},
/* USER_VALIDATION_RESPONSE                 */  {unexpected_command,    unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     user_validation},
};

int dispatch_command(command_e command, swap_app_context_t *context, unsigned char* input_buffer, unsigned int buffer_size, SendFunction send) {
    unexpected_command(context, input_buffer, buffer_size, send);
    StateCommandDispatcher handler = dispatcher_table[command][context->state];
    return handler(context, input_buffer, buffer_size, send);
}