#include "globals.h"
#include "commands.h"
#include "states.h"
#include "prompt_ui_display.h"
#include "validate_transaction.h"

void start_ui_display(void) {
    G_swap_ctx.state = WAITING_USER_VALIDATION;
    ui_validate_amounts();
}

int prompt_ui_display(const command_t *cmd) {
    // We don't care about the command passed as argument
    UNUSED(cmd);
    start_ui_display();
    return 0;
}
