#include "user_validation.h"
#include "currency_lib_calls.h"
#include "reply_error.h"
#include "swap_errors.h"

int user_validation(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, SendFunction send) {
    if (input_buffer_length != 1) {
        PRINTF("Error: Buffer should contain exactly one element");
        return reply_error(ctx, INTERNAL_ERROR, send);
    }
    if (input_buffer[0] == 0) { // user refused
        PRINTF("User refused transaction");
        return reply_error(ctx, USER_REFUSED, send); // strictly not a error
    }
    // user accepted
    unsigned char output_buffer[3] = {0x01, 0x90, 0x00};
    if (send(output_buffer, 3) < 0) {
        PRINTF("Error: Failed to send");
        return  -1;
    }
    ctx->state = INITIAL_STATE;
    // call application for creating payin transaction
    /*create_payin_transaction(
        ctx->received_transaction.
        */
    return 0;
}