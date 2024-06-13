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
#include "io_helpers.h"
#include "swap_errors.h"
#include "ux.h"

#define REFUSAL_TEXT_PART_1 "Incorrect transaction\nrejected by the\n"
#define REFUSAL_TEXT_PART_2 " app"
#define REFUSAL_TEXT_MAX_SIZE                                                         \
    ((sizeof(REFUSAL_TEXT_PART_1) - 1) + (sizeof(G_swap_ctx.payin_binary_name) - 1) + \
     (sizeof(REFUSAL_TEXT_PART_2) - 1) + 1)
static char refusal_text[REFUSAL_TEXT_MAX_SIZE];

// One of:
#define REVIEW_P1_TITLE   "Review transaction"
#define REVIEW_P1_CONFIRM "Sign transaction"

// Delimiter ' ' or '\n'

#define REVIEW_P2 "to"

// Delimiter ' ' or '\n'

// One of:
#define REVIEW_P3_SWAP "swap "
#define REVIEW_P3_SELL "sell "
#define REVIEW_P3_FUND "fund account"

// Delimiter ' ' or '\n'

// One of:
#define REVIEW_P4_SWAP "to "
#define REVIEW_P4_SELL "for "
#define REVIEW_P4_FUND "with "

// Maybe:
#define REVIEW_P5_CONFIRM "?"

// Calculate REVIEW_TITLE_MAX_SIZE with the SELL operation as it is the longest
#define REVIEW_TITLE_MAX_SIZE                                                          \
    (sizeof(REVIEW_P1_TITLE)                                  /* Review transaction */ \
     + 1                                                      /* ' ' */                \
     + sizeof(REVIEW_P2)                                      /* to */                 \
     + 1                                                      /* ' ' */                \
     + sizeof(REVIEW_P3_SELL)                                 /* sell */               \
     + (sizeof(G_swap_ctx.sell_transaction.in_currency) - 1)  /* TOKEN */              \
     + 1                                                      /* ' ' */                \
     + sizeof(REVIEW_P4_SELL)                                 /* for */                \
     + (sizeof(G_swap_ctx.sell_transaction.out_currency) - 1) /* CURRENCY */           \
     + 1)                                                     /* '\0' */

// Calculate REVIEW_CONFIRM_MAX_SIZE with the SELL operation as it is the longest
#define REVIEW_CONFIRM_MAX_SIZE                                                      \
    (sizeof(REVIEW_P1_CONFIRM)                                /* Sign transaction */ \
     + 1                                                      /* ' ' */              \
     + sizeof(REVIEW_P2)                                      /* to */               \
     + 1                                                      /* ' ' */              \
     + sizeof(REVIEW_P3_SELL)                                 /* sell */             \
     + (sizeof(G_swap_ctx.sell_transaction.in_currency) - 1)  /* TOKEN */            \
     + 1                                                      /* ' ' */              \
     + sizeof(REVIEW_P4_SELL)                                 /* for */              \
     + (sizeof(G_swap_ctx.sell_transaction.out_currency) - 1) /* CURRENCY */         \
     + 1                                                      /* ? */                \
     + 1)                                                     /* '\0' */

// Dynamic texts, dimensionned for worst case scenario
static char review_title[REVIEW_TITLE_MAX_SIZE];
static char review_confirm[REVIEW_CONFIRM_MAX_SIZE];

static void accept_tx(void) {
    nbgl_useCaseSpinner("Processing");
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

static nbgl_layoutTagValue_t pairs[5];
static nbgl_layoutTagValueList_t pair_list;
static nbgl_pageInfoLongPress_t info_long_press;

static void continue_review(void) {
    uint8_t index = 0;

    if (G_swap_ctx.subcommand != FUND && G_swap_ctx.subcommand != FUND_NG) {
        pairs[index].item = "Exchange partner";
        pairs[index].value = G_swap_ctx.partner.unprefixed_name;
        index++;
    }

    if (G_swap_ctx.subcommand == SELL || G_swap_ctx.subcommand == SELL_NG) {
        pairs[index].item = "Email";
        pairs[index].value = G_swap_ctx.sell_transaction.trader_email;
        index++;
    } else if (G_swap_ctx.subcommand == FUND || G_swap_ctx.subcommand == FUND_NG) {
        pairs[index].item = "User";
        pairs[index].value = G_swap_ctx.fund_transaction.user_id;
        index++;
    }

    pairs[index].item = "Send";
    pairs[index].value = G_swap_ctx.printable_send_amount;
    index++;

    if (G_swap_ctx.subcommand == FUND || G_swap_ctx.subcommand == FUND_NG) {
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
    info_long_press.text = review_confirm;
    info_long_press.longPressText = "Hold to sign";

    nbgl_useCaseStaticReview(&pair_list, &info_long_press, "Reject transaction", review_choice);
}

void ui_validate_amounts(void) {
    // The "to" is on the first line
    char delimitor_1 = ' ';
    char delimitor_2 = '\n';
    char delimitor_3 = ' ';
    const char *dyn_string_1;
    const char *dyn_string_2;
    const char *p3;
    const char *p4;
    switch (G_swap_ctx.subcommand) {
        case SWAP:
        case SWAP_NG:
            dyn_string_1 = G_swap_ctx.swap_transaction.currency_from;
            dyn_string_2 = G_swap_ctx.swap_transaction.currency_to;
            p3 = REVIEW_P3_SWAP;
            p4 = REVIEW_P4_SWAP;
            break;
        case SELL:
        case SELL_NG:
            dyn_string_1 = G_swap_ctx.sell_transaction.in_currency;
            dyn_string_2 = G_swap_ctx.sell_transaction.out_currency;
            p3 = REVIEW_P3_SELL;
            p4 = REVIEW_P4_SELL;
            break;
        case FUND:
        case FUND_NG:
            dyn_string_1 = "";
            dyn_string_2 = G_swap_ctx.fund_transaction.in_currency;
            p3 = REVIEW_P3_FUND;
            p4 = REVIEW_P4_FUND;
            break;
    }

    // Detect if we should display on 2 or 3 lines.
    if ((G_swap_ctx.subcommand == FUND || G_swap_ctx.subcommand == FUND_NG) ||
        (strlen(dyn_string_1) + strlen(dyn_string_2) >= 10)) {
        PRINTF("Review title and confirm on 3 lines\n");
        // Move the "to" to the second line with the operation
        delimitor_1 = '\n';
        delimitor_2 = ' ';
        delimitor_3 = '\n';
    }

    snprintf(review_title,
             sizeof(review_title),
             "%s%c%s%c%s%s%c%s%s",
             REVIEW_P1_TITLE,
             delimitor_1,
             REVIEW_P2,
             delimitor_2,
             p3,
             dyn_string_1,
             delimitor_3,
             p4,
             dyn_string_2);

    snprintf(review_confirm,
             sizeof(review_confirm),
             "%s%c%s%c%s%s%c%s%s%s",
             REVIEW_P1_CONFIRM,
             delimitor_1,
             REVIEW_P2,
             delimitor_2,
             p3,
             dyn_string_1,
             delimitor_3,
             p4,
             dyn_string_2,
             REVIEW_P5_CONFIRM);

    nbgl_useCaseReviewStart(&C_icon_exchange_64x64,
                            review_title,
                            NULL,
                            "Reject transaction",
                            continue_review,
                            rejectUseCaseChoice);
}

void display_signing_success(void) {
    nbgl_useCaseStatus("TRANSACTION\nSIGNED", true, ui_idle);
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
