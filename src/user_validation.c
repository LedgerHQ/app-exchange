#include "user_validation.h"
#include "currency_lib_calls.h"
#include "reply_error.h"
#include "swap_errors.h"

int user_validation(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, SendFunction send) {
    PRINTF("I am in user_validation\n");
    if (input_buffer_length != 1) {
        PRINTF("Error: Buffer should contain exactly one element\n");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }
    if (input_buffer[0] == 0) { // user refused
        PRINTF("User refused transaction\n");
        return reply_error(ctx, USER_REFUSED, send); // strictly speaking this is not an error
    }
    // user accepted
    unsigned char output_buffer[2] = {0x90, 0x00};
    if (send(output_buffer, 2) < 0) {
        PRINTF("Error: Failed to send\n");
        return  -1;
    }
    ctx->state = INITIAL_STATE;
    // create_payin_transaction(
    //     ctx->payin_coin_config,
    //     ctx->payin_coin_config_length,
    //     ctx->payin_binary_name,
    //     ctx->received_transaction.amount_to_provider.bytes,
    //     ctx->received_transaction.amount_to_provider.size,
    //     ctx->received_transaction.payin_address,
    //     ctx->received_transaction.payin_extra_id);
    return 0;
}