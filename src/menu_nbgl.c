#ifdef HAVE_NBGL

#include "commands.h"
#include "globals.h"
#include "glyphs.h"
#include "menu.h"
#include "nbgl_use_case.h"
#include "os.h"
#include "reply_error.h"
#include "send_function.h"
#include "swap_app_context.h"
#include "ux.h"

ux_state_t G_ux;
bolos_ux_params_t G_ux_params;

swap_app_context_t* application_context;
SendFunction send_function;

void on_accept()
{
    unsigned char output_buffer[2] = { 0x90, 0x00 };

    if (send_function(output_buffer, 2) < 0) {
        PRINTF("Error: Failed to send\n");
        return;
    }

    application_context->state = WAITING_SIGNING;
}

void on_reject()
{
    PRINTF("User refused transaction\n");

    reply_error(application_context, USER_REFUSED, send_function);
}

//////////////////////////

#define member_size(type, member) sizeof(((type*)0)->member)

struct ValidationInfo {
    char email[member_size(swap_app_context_t, sell_transaction.trader_email)];
    char send[MAX_PRINTABLE_AMOUNT_SIZE];
    char get[member_size(swap_app_context_t, printable_get_amount)];
    char fees[MAX_PRINTABLE_AMOUNT_SIZE];
    char provider[MAX_PRINTABLE_AMOUNT_SIZE];
    UserChoiseCallback OnAccept;
    UserChoiseCallback OnReject;
} validationInfo;

unsigned int io_accept(void)
{
    validationInfo.OnAccept();
    ui_idle();
    return 0;
}

unsigned int io_reject(void)
{
    validationInfo.OnReject();
    ui_idle();
    return 0;
}

static void reviewChoice(bool confirm)
{
    if (confirm) {
        io_accept();
    } else {
        io_reject();
    }
}

static nbgl_layoutTagValue_t tlv[7];
static rate_e _rate;
static subcommand_e _subcommand;
static bool displayTransactionPage(uint8_t page, nbgl_pageContent_t* content)
{
    uint8_t itemCount = 0;
    if (page == 0) {
        if (_subcommand == SELL) {
            tlv[itemCount].item = "Email";
            tlv[itemCount].value = validationInfo.email;
            itemCount++;
        } else if (_subcommand == FUND) {
            tlv[itemCount].item = "User";
            tlv[itemCount].value = validationInfo.email;
            itemCount++;
        }
        tlv[itemCount].item = "Send";
        tlv[itemCount].value = validationInfo.send;
        itemCount++;

        if (_subcommand == FUND) {
            tlv[itemCount].item = validationInfo.provider;
            tlv[itemCount].value = validationInfo.get;
            itemCount++;
        } else if (_rate == FLOATING) {
            tlv[itemCount].item = "Get estimated";
            tlv[itemCount].value = validationInfo.get;
            itemCount++;
        } else {
            tlv[itemCount].item = "Get";
            tlv[itemCount].value = validationInfo.get;
            itemCount++;
        }

        tlv[itemCount].item = "Fees";
        tlv[itemCount].value = validationInfo.fees;
        itemCount++;

        content->type = TAG_VALUE_LIST;
        content->tagValueList.nbPairs = itemCount;
        content->tagValueList.pairs = (nbgl_layoutTagValue_t*)tlv;
    } else if (page == 1) {
        content->type = INFO_LONG_PRESS,
        content->infoLongPress.icon = &C_badge_transaction_56;
        content->infoLongPress.text = "Review transaction";
        content->infoLongPress.longPressText = "Hold to confirm";
    }
    return true;
}
static void reviewContinue(void)
{
    nbgl_useCaseRegularReview(0, 2, "Reject", NULL, displayTransactionPage, reviewChoice);
}

static void buildFirstPage(void)
{
    nbgl_useCaseReviewStart(&C_badge_transaction_56, "Review transaction", NULL, "Reject", reviewContinue, io_reject);
}

void ux_confirm(rate_e rate, subcommand_e subcommand)
{
    _rate = rate;
    _subcommand = subcommand;
    buildFirstPage();
}

void ui_validate_amounts(rate_e rate,
    subcommand_e subcommand,
    swap_app_context_t* ctx,
    char* send_amount,
    char* fees_amount,
    SendFunction send)
{
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

void ux_init()
{
    UX_INIT();
}

void app_quit(void)
{
    os_sched_exit(-1);
}

static bool settingsNavCallback(uint8_t page, nbgl_pageContent_t* content)
{
    static const char* const infoTypes[] = { "Version", "Exchange App" };
    static const char* const infoContents[] = { APPVERSION, "(c) 2022 Ledger" };

    content->type = INFOS_LIST;
    content->infosList.nbInfos = 2;
    content->infosList.infoTypes = (const char**)infoTypes;
    content->infosList.infoContents = (const char**)infoContents;
    return true;
}

static void settingsControlsCallback(int token, uint8_t index)
{
}

void ui_menu_settings(void)
{
    nbgl_useCaseSettings("Exchange settings", 0, 1, true, ui_idle, settingsNavCallback, settingsControlsCallback);
}

void ui_idle(void)
{
    nbgl_useCaseHome(APPNAME, NULL, APPNAME, true, ui_menu_settings, app_quit);
}

unsigned char io_event(__attribute__((unused)) unsigned char channel)
{
    // nothing done with the event, throw an error on the transport layer if
    // needed
    // can't have more than one tag in the reply, not supported yet.
    switch (G_io_seproxyhal_spi_buffer[0]) {
    case SEPROXYHAL_TAG_FINGER_EVENT:
        UX_FINGER_EVENT(G_io_seproxyhal_spi_buffer);
        break;

    case SEPROXYHAL_TAG_STATUS_EVENT:
        if (G_io_apdu_media == IO_APDU_MEDIA_USB_HID && !(U4BE(G_io_seproxyhal_spi_buffer, 3) & SEPROXYHAL_TAG_STATUS_EVENT_FLAG_USB_POWERED)) {
            THROW(EXCEPTION_IO_RESET);
        }
        // no break is intentional
    default:
        UX_DEFAULT_EVENT();
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

unsigned short io_exchange_al(unsigned char channel, unsigned short tx_len)
{
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
            return 0; // nothing received from the master so far (it's a tx
                      // transaction)
        } else {
            return io_seproxyhal_spi_recv(G_io_apdu_buffer, sizeof(G_io_apdu_buffer), 0);
        }

    default:
        THROW(INVALID_PARAMETER);
    }
    return 0;
}

#endif // HAVE_NBGL