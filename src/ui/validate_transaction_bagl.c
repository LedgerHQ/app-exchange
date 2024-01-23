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
UX_STEP_NOCB(step_1_all, pnn,
{
    &C_icon_eye,
    "Review",
    "transaction",
});
UX_STEP_NOCB(step_2_not_fund, bnnn_paging,
{
    .title = "Exchange partner",
    .text = G_swap_ctx.partner.unprefixed_name,
});
UX_STEP_NOCB(step_3_sell, bnnn_paging,
{
    .title = "Email",
    .text = G_swap_ctx.sell_transaction.trader_email,
});
UX_STEP_NOCB(step_3_fund, bnnn_paging,
{
    .title = "User",
    .text = G_swap_ctx.fund_transaction.user_id,
});
UX_STEP_NOCB(step_4_all, bnnn_paging,
{
    .title = "Send",
    .text = G_swap_ctx.printable_send_amount,
});
UX_STEP_NOCB(step_5_fund, bnnn_paging,
{
    .title = G_swap_ctx.partner.prefixed_name,
    .text = G_swap_ctx.account_name,
});
UX_STEP_NOCB(step_5_not_fund_fixed_rate, bnnn_paging,
{
    .title = "Get",
    .text = G_swap_ctx.printable_get_amount,
});
UX_STEP_NOCB(step_5_not_fund_floating_rate, bnnn_paging,
{
    .title = "Get estimated",
    .text = G_swap_ctx.printable_get_amount,
});
UX_STEP_NOCB(step_6_all, bnnn_paging,
{
    .title = "Fees",
    .text = G_swap_ctx.printable_fees_amount,
});
UX_STEP_CB(step_7_all, pbb, on_accept(NULL),
{
    &C_icon_validate_14,
    "Accept",
    "and send",
});
UX_STEP_CB(step_8_all, pb, on_reject(NULL),
{
    &C_icon_crossmark,
    "Reject",
});

// clang-format on

// 8 steps max + FLOW_END_STEP
const ux_flow_step_t *ux_confirm_flow[9];

void ui_validate_amounts(void) {
    int step = 0;

    ux_confirm_flow[step++] = &step_1_all;

    if (G_swap_ctx.subcommand != FUND && G_swap_ctx.subcommand != FUND_NG) {
        ux_confirm_flow[step++] = &step_2_not_fund;
    }

    if (G_swap_ctx.subcommand == SELL || G_swap_ctx.subcommand == SELL_NG) {
        ux_confirm_flow[step++] = &step_3_sell;
    } else if (G_swap_ctx.subcommand == FUND || G_swap_ctx.subcommand == FUND_NG) {
        ux_confirm_flow[step++] = &step_3_fund;
    }

    ux_confirm_flow[step++] = &step_4_all;

    if (G_swap_ctx.subcommand == FUND || G_swap_ctx.subcommand == FUND_NG) {
        ux_confirm_flow[step++] = &step_5_fund;
    } else {
        if (G_swap_ctx.rate == FLOATING) {
            ux_confirm_flow[step++] = &step_5_not_fund_floating_rate;
        } else {
            ux_confirm_flow[step++] = &step_5_not_fund_fixed_rate;
        }
    }

    ux_confirm_flow[step++] = &step_6_all;
    ux_confirm_flow[step++] = &step_7_all;
    ux_confirm_flow[step++] = &step_8_all;
    ux_confirm_flow[step++] = FLOW_END_STEP;

    // /!\ Remember to update ux_confirm_flow size if adding steps

    ux_flow_init(0, ux_confirm_flow, NULL);
}

#endif
