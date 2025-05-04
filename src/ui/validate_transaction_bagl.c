#ifdef HAVE_BAGL

#include "menu.h"
#include "validate_transaction.h"
#include "ux.h"
#include "os.h"
#include "globals.h"
#include "glyphs.h"
#include "io.h"
#include "io_helpers.h"
#include "commands.h"
#include "swap_errors.h"

static void on_accept(__attribute__((unused)) const bagl_element_t *e) {
    reply_success();
    G_swap_ctx.state = WAITING_SIGNING;
    ui_idle();
}

static void on_reject(__attribute__((unused)) const bagl_element_t *e) {
    PRINTF("User refused transaction\n");
    reply_error(USER_REFUSED);
    G_swap_ctx.state = INITIAL_STATE;
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

#ifdef DIRECT_CALLS_API
char G_application_name[BOLOS_APPNAME_MAX_SIZE_B + 1];
char G_to_print[sizeof(G_swap_ctx.printable_send_amount)] = {0};
char G_to_print_fees[sizeof(G_swap_ctx.printable_send_amount)] = {0};

static void on_direct_amount_review_accept(__attribute__((unused)) const bagl_element_t *e) {
    reply_success();
    ui_idle();
}

static void on_direct_amount_review_reject(__attribute__((unused)) const bagl_element_t *e) {
    reply_error(USER_REFUSED);
    ui_idle();
}

UX_STEP_NOCB(step_1_direct_amount_review,
             bnnn_paging,
             {
                 .title = "Testing application",
                 .text = G_application_name,
             });
UX_STEP_NOCB(step_2_direct_amount_review,
             bnnn_paging,
             {
                 .title = "Amount displayed:",
                 .text = G_to_print,
             });
UX_STEP_NOCB(step_3_direct_amount_review,
             bnnn_paging,
             {
                 .title = "as fees:",
                 .text = G_to_print_fees,
             });
UX_STEP_CB(step_4_direct_amount_review,
           pbb,
           on_direct_amount_review_accept(NULL),
           {
               &C_icon_validate_14,
               "Approve",
               "formatting",
           });
UX_STEP_CB(step_5_direct_amount_review,
           pb,
           on_direct_amount_review_reject(NULL),
           {
               &C_icon_crossmark,
               "Reject",
           });

void direct_amount_review(const char *application_name,
                          const char *to_print,
                          const char *to_print_as_fees) {
    memcpy(G_application_name, application_name, sizeof(G_application_name));
    memcpy(G_to_print, to_print, sizeof(G_to_print));
    memcpy(G_to_print_fees, to_print_as_fees, sizeof(G_to_print_fees));

    ux_confirm_flow[0] = &step_1_direct_amount_review;
    ux_confirm_flow[1] = &step_2_direct_amount_review;
    ux_confirm_flow[2] = &step_3_direct_amount_review;
    ux_confirm_flow[3] = &step_4_direct_amount_review;
    ux_confirm_flow[4] = &step_5_direct_amount_review;
    ux_confirm_flow[5] = FLOW_END_STEP;

    ux_flow_init(0, ux_confirm_flow, NULL);
}

#endif  // DIRECT_CALLS_API
#endif  // HAVE_BAGL
