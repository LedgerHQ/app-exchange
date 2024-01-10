#ifdef HAVE_BAGL

#include "menu.h"
#include "validate_transaction.h"
#include "ux.h"
#include "os.h"
#include "globals.h"
#include "glyphs.h"
#include "io.h"
#include "commands.h"

static void on_accept(__attribute__((unused)) const bagl_element_t *e) {
    reply_success();
    G_swap_ctx.state = WAITING_SIGNING;
    ui_idle();
}

static void on_reject(__attribute__((unused)) const bagl_element_t *e) {
    PRINTF("User refused transaction\n");
    reply_error(USER_REFUSED);
    ui_idle();
}

// clang-format off
UX_STEP_NOCB(ux_confirm_flow_1_step, pnn,
{
    &C_icon_eye,
    "Review",
    "transaction",
});
UX_STEP_NOCB(ux_confirm_flow_1_2_step, bnnn_paging,
{
    .title = "Email",
    .text = G_swap_ctx.sell_transaction.trader_email,
});
UX_STEP_NOCB(ux_confirm_flow_1_3_step, bnnn_paging,
{
    .title = "User",
    .text = G_swap_ctx.fund_transaction.user_id,
});
UX_STEP_NOCB(ux_confirm_flow_2_step, bnnn_paging,
{
    .title = "Send",
    .text = G_swap_ctx.printable_send_amount,
});
UX_STEP_NOCB(ux_confirm_flow_3_step, bnnn_paging,
{
    .title = "Get",
    .text = G_swap_ctx.printable_get_amount,
});
UX_STEP_NOCB(ux_confirm_flow_3_floating_step, bnnn_paging,
{
    .title = "Get estimated",
    .text = G_swap_ctx.printable_get_amount,
});
UX_STEP_NOCB(ux_confirm_flow_3_2_step, bnnn_paging,
{
    .title = G_swap_ctx.partner.prefixed_name,
    .text = G_swap_ctx.account_name,
});
UX_STEP_NOCB(ux_confirm_flow_4_step, bnnn_paging,
{
    .title = "Fees",
    .text = G_swap_ctx.printable_fees_amount,
});
UX_STEP_CB(ux_confirm_flow_5_step, pbb, on_accept(NULL),
{
    &C_icon_validate_14,
    "Accept",
    "and send",
});
UX_STEP_CB(ux_confirm_flow_6_step, pb, on_reject(NULL),
{
    &C_icon_crossmark,
    "Reject",
});

// clang-format on
const ux_flow_step_t *ux_confirm_flow[8];

void ui_validate_amounts(void) {
    int step = 0;

    ux_confirm_flow[step++] = &ux_confirm_flow_1_step;

    if (G_swap_ctx.subcommand == SELL || G_swap_ctx.subcommand == SELL_NG) {
        ux_confirm_flow[step++] = &ux_confirm_flow_1_2_step;
    } else if (G_swap_ctx.subcommand == FUND || G_swap_ctx.subcommand == FUND_NG) {
        ux_confirm_flow[step++] = &ux_confirm_flow_1_3_step;
    }

    ux_confirm_flow[step++] = &ux_confirm_flow_2_step;

    if (G_swap_ctx.subcommand == FUND || G_swap_ctx.subcommand == FUND_NG) {
        ux_confirm_flow[step++] = &ux_confirm_flow_3_2_step;
    } else if (G_swap_ctx.rate == FLOATING) {
        ux_confirm_flow[step++] = &ux_confirm_flow_3_floating_step;
    } else {
        ux_confirm_flow[step++] = &ux_confirm_flow_3_step;
    }

    ux_confirm_flow[step++] = &ux_confirm_flow_4_step;
    ux_confirm_flow[step++] = &ux_confirm_flow_5_step;
    ux_confirm_flow[step++] = &ux_confirm_flow_6_step;
    ux_confirm_flow[step++] = FLOW_END_STEP;

    ux_flow_init(0, ux_confirm_flow, NULL);
}

#endif
