#include "start_signing_transaction.h"
#include "currency_lib_calls.h"
#include "reply_error.h"

int start_signing_transaction(subcommand_e subcommand,
                              swap_app_context_t *ctx,
                              const buf_t *input,
                              SendFunction send) {
    G_io_apdu_buffer[0] = 0x90;
    G_io_apdu_buffer[1] = 0x00;
    io_exchange(CHANNEL_APDU | IO_RETURN_AFTER_TX, 2);
    ctx->state = INITIAL_STATE;
    static create_transaction_parameters_t lib_in_out_params;

    lib_in_out_params.fee_amount = ctx->transaction_fee;
    lib_in_out_params.fee_amount_length = ctx->transaction_fee_length;
    lib_in_out_params.coin_configuration = ctx->payin_coin_config.bytes;
    lib_in_out_params.coin_configuration_length = ctx->payin_coin_config.size;

    if (subcommand == SWAP) {
        lib_in_out_params.amount = ctx->received_transaction.amount_to_provider.bytes;
        lib_in_out_params.amount_length = ctx->received_transaction.amount_to_provider.size;
        lib_in_out_params.destination_address = ctx->received_transaction.payin_address;
        lib_in_out_params.destination_address_extra_id = ctx->received_transaction.payin_extra_id;
    }

    if (subcommand == SELL) {
        lib_in_out_params.amount = ctx->sell_transaction.in_amount.bytes;
        lib_in_out_params.amount_length = ctx->sell_transaction.in_amount.size;
        lib_in_out_params.destination_address = ctx->sell_transaction.in_address;
        lib_in_out_params.destination_address_extra_id = ctx->received_transaction.payin_extra_id;
    }

    create_payin_transaction(ctx->payin_binary_name, &lib_in_out_params);

    return 0;
}
