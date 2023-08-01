#include "start_signing_transaction.h"
#include "currency_lib_calls.h"
#include "globals.h"
#include "io.h"

int start_signing_transaction(const command_t *cmd) {
    int ret = 0;
    G_io_apdu_buffer[0] = 0x90;
    G_io_apdu_buffer[1] = 0x00;
    io_exchange(CHANNEL_APDU | IO_RETURN_AFTER_TX, 2);
    G_swap_ctx.state = INITIAL_STATE;
    static create_transaction_parameters_t lib_in_out_params;

    lib_in_out_params.fee_amount = G_swap_ctx.transaction_fee;
    lib_in_out_params.fee_amount_length = G_swap_ctx.transaction_fee_length;
    lib_in_out_params.coin_configuration = G_swap_ctx.payin_coin_config.bytes;
    lib_in_out_params.coin_configuration_length = G_swap_ctx.payin_coin_config.size;

    if (cmd->subcommand == SWAP || cmd->subcommand == SWAP_NG) {
        lib_in_out_params.amount = G_swap_ctx.received_transaction.amount_to_provider.bytes;
        lib_in_out_params.amount_length = G_swap_ctx.received_transaction.amount_to_provider.size;
        lib_in_out_params.destination_address = G_swap_ctx.received_transaction.payin_address;
        lib_in_out_params.destination_address_extra_id =
            G_swap_ctx.received_transaction.payin_extra_id;
    }

    if (cmd->subcommand == SELL || cmd->subcommand == SELL_NG) {
        lib_in_out_params.amount = G_swap_ctx.sell_transaction.in_amount.bytes;
        lib_in_out_params.amount_length = G_swap_ctx.sell_transaction.in_amount.size;
        lib_in_out_params.destination_address = G_swap_ctx.sell_transaction.in_address;
        // Empty string, needed by application library API but does not have sense in SELL context
        lib_in_out_params.destination_address_extra_id = G_swap_ctx.sell_transaction_extra_id;
    }

    if (cmd->subcommand == FUND || cmd->subcommand == FUND_NG) {
        lib_in_out_params.amount = G_swap_ctx.fund_transaction.in_amount.bytes;
        lib_in_out_params.amount_length = G_swap_ctx.fund_transaction.in_amount.size;
        lib_in_out_params.destination_address = G_swap_ctx.fund_transaction.in_address;
        // Empty string, needed by application library API but does not have sense in FUND context
        lib_in_out_params.destination_address_extra_id = G_swap_ctx.fund_transaction_extra_id;
    }

    ret = create_payin_transaction(G_swap_ctx.payin_binary_name, &lib_in_out_params);
    // Write G_swap_ctx.state AFTER coming back to exchange to avoid erasure by the app
    G_swap_ctx.state = SIGN_FINISHED;

    return ret;
}
