#ifdef HAVE_NBGL

#include "commands.h"
#include "globals.h"
#include "glyphs.h"
#include "menu.h"
#include "validate_transaction.h"
#include "nbgl_use_case.h"
#include "nbgl_page.h"
#include "nbgl_layout.h"
#include "os.h"
#include "io.h"
#include "ux.h"

#define SPINNER_TEXT_PART_1 "Starting the "
#define SPINNER_TEXT_PART_2 " app to sign the transaction"
static char spinner_text[(sizeof(SPINNER_TEXT_PART_1) - 1)
                         + BOLOS_APPNAME_MAX_SIZE_B
                         + (sizeof(SPINNER_TEXT_PART_2) - 1)
                         + 1];


#define REFUSAL_TEXT_PART_1 "Incorrect transaction\nrejected by the\n"
#define REFUSAL_TEXT_PART_2 " app"
static char refusal_text[(sizeof(REFUSAL_TEXT_PART_1) - 1)
                         + BOLOS_APPNAME_MAX_SIZE_B
                         + (sizeof(REFUSAL_TEXT_PART_2) - 1)
                         + 1];

static void accept_tx(void) {
    snprintf(spinner_text,
             sizeof(spinner_text),
             "%s%s%s",
             SPINNER_TEXT_PART_1,
             G_swap_ctx.payin_binary_name,
             SPINNER_TEXT_PART_2);
    nbgl_useCaseSpinner(spinner_text);
    reply_success();
    G_swap_ctx.state = WAITING_SIGNING;
}

static void reject_tx(void) {
    PRINTF("User refused transaction\n");
    reply_error(USER_REFUSED);
    nbgl_useCaseStatus("Transaction\nrejected", false, ui_idle);
}

// If the user asks for message rejection, ask for confirmation
static void rejectUseCaseChoice(void) {
    nbgl_useCaseConfirm("Reject transaction?",
                        NULL,
                        "Yes, reject",
                        "Go back to transaction",
                        reject_tx);
}

static void review_choice(bool confirm) {
    if (confirm) {
        accept_tx();
    } else {
        rejectUseCaseChoice();
    }
}

static nbgl_layoutTagValue_t pairs[4];
static nbgl_layoutTagValueList_t pair_list;
static nbgl_pageInfoLongPress_t info_long_press;

static void continue_review(void) {
    uint8_t index = 0;

    if (G_swap_ctx.subcommand == SELL) {
        pairs[index].item = "Email";
        pairs[index].value = G_swap_ctx.sell_transaction.trader_email;
        index++;
    } else if (G_swap_ctx.subcommand == FUND) {
        pairs[index].item = "User";
        pairs[index].value = G_swap_ctx.fund_transaction.user_id;
        index++;
    }

    pairs[index].item = "Send";
    pairs[index].value = G_swap_ctx.printable_send_amount;
    index++;

    if (G_swap_ctx.subcommand == FUND) {
        pairs[index].item = G_swap_ctx.partner.prefixed_name;
        pairs[index].value = G_swap_ctx.printable_get_amount;
        index++;
    } else {
        if (G_swap_ctx.rate == FLOATING) {
            pairs[index].item = "Get estimated";
        } else {
            pairs[index].item = "Get";
        }
        pairs[index].value = G_swap_ctx.printable_get_amount;
        index++;
    }

    pairs[index].item = "Fees";
    pairs[index].value = G_swap_ctx.printable_fees_amount;
    index++;

    pair_list.nbMaxLinesForValue = 0;
    pair_list.nbPairs = index;
    pair_list.pairs = pairs;

    info_long_press.icon = &C_icon_exchange_64x64;
    info_long_press.text = "Sign transaction";
    info_long_press.longPressText = "Hold to sign";

    nbgl_useCaseStaticReview(&pair_list, &info_long_press, "Reject", review_choice);
}

void ui_validate_amounts(void) {
    nbgl_useCaseReviewStart(&C_icon_exchange_64x64,
                            "Review transaction",
                            NULL,
                            "Reject",
                            continue_review,
                            rejectUseCaseChoice);
}

void display_signing_success(void) {
    nbgl_useCaseStatus("TRANSACTION\nSUCCESS", true, ui_idle);
}

void display_signing_failure(const char *appname) {
    snprintf(refusal_text,
             sizeof(refusal_text),
             "%s%s%s",
             REFUSAL_TEXT_PART_1,
             appname,
             REFUSAL_TEXT_PART_2);
    nbgl_useCaseStatus(refusal_text, false, ui_idle);
}

#endif  // HAVE_NBGL
