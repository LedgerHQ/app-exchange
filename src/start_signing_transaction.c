#include "start_signing_transaction.h"
#include "currency_lib_calls.h"
#include "globals.h"
#include "io_helpers.h"

int start_signing_transaction(const command_t *cmd) {
    // Inform the caller that we will call the lib app
    if (instant_reply_success() < 0) {
        PRINTF("Error: failed to send\n");
        return -1;
    }

    // Create the variable given to the signing app. It's placed in BSS section to save RAM
    // (heap is shared, stack is not)
    static create_transaction_parameters_t lib_in_out_params;

    lib_in_out_params.fee_amount = G_swap_ctx.transaction_fee;
    lib_in_out_params.fee_amount_length = G_swap_ctx.transaction_fee_length;
    lib_in_out_params.coin_configuration_length = G_swap_ctx.paying_sub_coin_config_size;

    // Small patch to give the app NULL pointer if there is no sub coin conf (Solana checks it)
    // Solana should be changed to remove this unnecessary check, in the meantime we workaround here
    if (G_swap_ctx.paying_sub_coin_config_size == 0) {
        lib_in_out_params.coin_configuration = NULL;
    } else {
        lib_in_out_params.coin_configuration = G_swap_ctx.paying_sub_coin_config;
    }

    if (cmd->subcommand == SWAP || cmd->subcommand == SWAP_NG) {
        lib_in_out_params.amount = G_swap_ctx.swap_transaction.amount_to_provider.bytes;
        lib_in_out_params.amount_length = G_swap_ctx.swap_transaction.amount_to_provider.size;
        lib_in_out_params.destination_address = G_swap_ctx.swap_transaction.payin_address;
        if (G_swap_ctx.swap_transaction.payin_extra_data.size == 33) {
            PRINTF("Using extra data %.*H\n",
                   G_swap_ctx.swap_transaction.payin_extra_data.size,
                   G_swap_ctx.swap_transaction.payin_extra_data.bytes);
            lib_in_out_params.destination_address_extra_id =
                (char *) G_swap_ctx.swap_transaction.payin_extra_data.bytes;
        } else {
            PRINTF("Using native payin_extra_id %s\n", G_swap_ctx.swap_transaction.payin_extra_id);
            lib_in_out_params.destination_address_extra_id =
                G_swap_ctx.swap_transaction.payin_extra_id;
        }
    }

    if (cmd->subcommand == SELL || cmd->subcommand == SELL_NG) {
        lib_in_out_params.amount = G_swap_ctx.sell_transaction.in_amount.bytes;
        lib_in_out_params.amount_length = G_swap_ctx.sell_transaction.in_amount.size;
        lib_in_out_params.destination_address = G_swap_ctx.sell_transaction.in_address;
        lib_in_out_params.destination_address_extra_id = G_swap_ctx.sell_transaction.in_extra_id;
    }

    if (cmd->subcommand == FUND || cmd->subcommand == FUND_NG) {
        lib_in_out_params.amount = G_swap_ctx.fund_transaction.in_amount.bytes;
        lib_in_out_params.amount_length = G_swap_ctx.fund_transaction.in_amount.size;
        lib_in_out_params.destination_address = G_swap_ctx.fund_transaction.in_address;
        lib_in_out_params.destination_address_extra_id = G_swap_ctx.fund_transaction.in_extra_id;
    }

    create_payin_transaction(&lib_in_out_params);
    G_swap_ctx.state = SIGN_FINISHED;

    // The called app refusing to sign is NOT an handler error, we report a success
    return 0;
}
