#include "menu.h"
#include "ux.h"
#include "os.h"
#include "globals.h"
#include "glyphs.h"
#include "swap_app_context.h"
#include "send_function.h"
#include "reply_error.h"
#include "commands.h"

ux_state_t G_ux;
bolos_ux_params_t G_ux_params;

swap_app_context_t *application_context;
SendFunction send_function;

void on_accept() {
    unsigned char output_buffer[2] = {0x90, 0x00};

    if (send_function(output_buffer, 2) < 0) {
        PRINTF("Error: Failed to send\n");
        return;
    }

    application_context->state = WAITING_SIGNING;
}

void on_reject() {
    PRINTF("User refused transaction\n");

    reply_error(application_context, USER_REFUSED, send_function);
}

// clang-format off
UX_STEP_NOCB(ux_idle_flow_1_step, nn,
{
    "Exchange",
    "is ready",
});
UX_STEP_NOCB(ux_idle_flow_2_step, bn,
{
    "Version",
    APPVERSION,
});
UX_STEP_VALID(ux_idle_flow_3_step, pb, os_sched_exit(-1),
{
    &C_icon_dashboard_x,
    "Quit",
});

UX_FLOW(ux_idle_flow,
&ux_idle_flow_1_step,
&ux_idle_flow_2_step,
&ux_idle_flow_3_step,
FLOW_LOOP);
// clang-format on

//////////////////////////

#define member_size(type, member) sizeof(((type *) 0)->member)

struct ValidationInfo {
    char email[member_size(swap_app_context_t, sell_transaction.trader_email)];
    char send[PRINTABLE_AMOUNT_SIZE];
    char get[member_size(swap_app_context_t, printable_get_amount)];
    char fees[PRINTABLE_AMOUNT_SIZE];
    char provider[PRINTABLE_AMOUNT_SIZE];
    UserChoiseCallback OnAccept;
    UserChoiseCallback OnReject;
} validationInfo;

unsigned int io_accept(__attribute__((unused)) const bagl_element_t *e) {
    validationInfo.OnAccept();
    ui_idle();
    return 0;
}

unsigned int io_reject(__attribute__((unused)) const bagl_element_t *e) {
    validationInfo.OnReject();
    ui_idle();
    return 0;
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
    .text = validationInfo.email,
});
UX_STEP_NOCB(ux_confirm_flow_1_3_step, bnnn_paging,
{
    .title = "User",
    .text = validationInfo.email,
});
UX_STEP_NOCB(ux_confirm_flow_2_step, bnnn_paging,
{
    .title = "Send",
    .text = validationInfo.send,
});
UX_STEP_NOCB(ux_confirm_flow_3_step, bnnn_paging,
{
    .title = "Get",
    .text = validationInfo.get,
});
UX_STEP_NOCB(ux_confirm_flow_3_floating_step, bnnn_paging,
{
    .title = "Get estimated",
    .text = validationInfo.get,
});
UX_STEP_NOCB(ux_confirm_flow_3_2_step, bnnn_paging,
{
    .title = validationInfo.provider,
    .text = validationInfo.get,
});
UX_STEP_NOCB(ux_confirm_flow_4_step, bnnn_paging,
{
    .title = "Fees",
    .text = validationInfo.fees,
});
UX_STEP_CB(ux_confirm_flow_5_step, pbb, io_accept(NULL),
{
    &C_icon_validate_14,
    "Accept",
    "and send",
});
UX_STEP_CB(ux_confirm_flow_6_step, pb, io_reject(NULL),
{
    &C_icon_crossmark,
    "Reject",
});

// clang-format on
const ux_flow_step_t *ux_confirm_flow[8];

void ux_confirm(rate_e rate, subcommand_e subcommand) {
    int step = 0;
    ux_confirm_flow[step++] = &ux_confirm_flow_1_step;
    if (subcommand == SELL) {
        ux_confirm_flow[step++] = &ux_confirm_flow_1_2_step;
    } else if (subcommand == FUND) {
        ux_confirm_flow[step++] = &ux_confirm_flow_1_3_step;
    }
    ux_confirm_flow[step++] = &ux_confirm_flow_2_step;
    if (subcommand == FUND) {
        ux_confirm_flow[step++] = &ux_confirm_flow_3_2_step;
    } else if (rate == FLOATING) {
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

void ui_validate_amounts(rate_e rate,
                         subcommand_e subcommand,
                         swap_app_context_t *ctx,
                         char *send_amount,
                         char *fees_amount,
                         SendFunction send) {
    application_context = ctx;
    send_function = send;

    strncpy(validationInfo.send, send_amount, sizeof(validationInfo.send));
    validationInfo.send[sizeof(validationInfo.send) - 1] = '\x00';

    strncpy(validationInfo.get, ctx->printable_get_amount, sizeof(validationInfo.get));
    validationInfo.get[sizeof(validationInfo.get) - 1] = '\x00';

    strncpy(validationInfo.fees, fees_amount, sizeof(validationInfo.fees));
    validationInfo.fees[sizeof(validationInfo.fees) - 1] = '\x00';

    validationInfo.OnAccept = on_accept;
    validationInfo.OnReject = on_reject;

    if (subcommand == SELL) {
        strncpy(validationInfo.email,
                ctx->sell_transaction.trader_email,
                sizeof(validationInfo.email));
        validationInfo.email[sizeof(validationInfo.email) - 1] = '\x00';
    }

    if (subcommand == FUND) {
        strncpy(validationInfo.email, ctx->fund_transaction.user_id, sizeof(validationInfo.email));
        validationInfo.email[sizeof(validationInfo.email) - 1] = '\x00';

        strncpy(validationInfo.provider, "To ", 3);

        strncpy(validationInfo.provider + 3,
                ctx->partner.name,
                sizeof(validationInfo.provider) - 4);
        validationInfo.provider[sizeof(validationInfo.provider) - 1] = '\x00';
    }
    ux_confirm(rate, subcommand);
}

void ux_init() {
    UX_INIT();
}

void ui_idle(void) {
    // reserve a display stack slot if none yet
    if (G_ux.stack_count == 0) {
        ux_stack_push();
    }
    ux_flow_init(0, ux_idle_flow, NULL);
}

// override point, but nothing more to do
void io_seproxyhal_display(const bagl_element_t *element) {
    io_seproxyhal_display_default((bagl_element_t *) element);
}

unsigned char io_event(__attribute__((unused)) unsigned char channel) {
    // nothing done with the event, throw an error on the transport layer if
    // needed
    // can't have more than one tag in the reply, not supported yet.
    switch (G_io_seproxyhal_spi_buffer[0]) {
        case SEPROXYHAL_TAG_FINGER_EVENT:
            UX_FINGER_EVENT(G_io_seproxyhal_spi_buffer);
            break;

        case SEPROXYHAL_TAG_BUTTON_PUSH_EVENT: {
            UX_BUTTON_PUSH_EVENT(G_io_seproxyhal_spi_buffer);
            break;
        }
        case SEPROXYHAL_TAG_STATUS_EVENT:
            if (G_io_apdu_media == IO_APDU_MEDIA_USB_HID &&
                !(U4BE(G_io_seproxyhal_spi_buffer, 3) &
                  SEPROXYHAL_TAG_STATUS_EVENT_FLAG_USB_POWERED)) {
                THROW(EXCEPTION_IO_RESET);
            }
            // no break is intentional
        default:
            UX_DEFAULT_EVENT();
            break;

        case SEPROXYHAL_TAG_DISPLAY_PROCESSED_EVENT:
            UX_DISPLAYED_EVENT({});
            break;

        case SEPROXYHAL_TAG_TICKER_EVENT:
            UX_TICKER_EVENT(G_io_seproxyhal_spi_buffer, {});
            break;
    }

    // close the event if not done previously (by a display or whatever)
    if (!io_seproxyhal_spi_is_status_sent()) {
        io_seproxyhal_general_status();
    }

    // command has been processed, DO NOT reset the current APDU transport
    return 1;
}

unsigned short io_exchange_al(unsigned char channel, unsigned short tx_len) {
    switch (channel & ~(IO_FLAGS)) {
        case CHANNEL_KEYBOARD:
            break;

        // multiplexed io exchange over a SPI channel and TLV encapsulated protocol
        case CHANNEL_SPI:
            if (tx_len) {
                io_seproxyhal_spi_send(G_io_apdu_buffer, tx_len);

                if (channel & IO_RESET_AFTER_REPLIED) {
                    reset();
                }
                return 0;  // nothing received from the master so far (it's a tx
                           // transaction)
            } else {
                return io_seproxyhal_spi_recv(G_io_apdu_buffer, sizeof(G_io_apdu_buffer), 0);
            }

        default:
            THROW(INVALID_PARAMETER);
    }
    return 0;
}
