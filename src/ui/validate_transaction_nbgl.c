#ifdef HAVE_NBGL

#include "commands.h"
#include "globals.h"
#include "glyphs.h"
#include "menu.h"
#include "validate_transaction.h"
#include "nbgl_use_case.h"
#include "os.h"
#include "io.h"
#include "io_helpers.h"
#include "swap_errors.h"
#include "ux.h"
#include "icons.h"

/*****************************
 *     TITLE AND CONFIRM     *
 *****************************/

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

// P4 = 'FROM currency' for SWAP and SELL, '' for FUND

// Delimiter ' ' or '\n'

// One of:
#define REVIEW_P5_SWAP "to "
#define REVIEW_P5_SELL "for "
#define REVIEW_P5_FUND "with "

// P6 = 'TO currency' for SWAP and SELL, 'FROM currency' for FUND

// Maybe:
#define REVIEW_P7_CONFIRM "?"

// Calculate REVIEW_TITLE_MAX_SIZE with the SELL operation as it is the longest
#define REVIEW_TITLE_MAX_SIZE                                                          \
    (sizeof(REVIEW_P1_TITLE)                                  /* Review transaction */ \
     + 1                                                      /* ' ' */                \
     + sizeof(REVIEW_P2)                                      /* to */                 \
     + 1                                                      /* ' ' */                \
     + sizeof(REVIEW_P3_SELL)                                 /* sell */               \
     + (sizeof(G_swap_ctx.sell_transaction.in_currency) - 1)  /* TOKEN */              \
     + 1                                                      /* ' ' */                \
     + sizeof(REVIEW_P5_SELL)                                 /* for */                \
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
     + sizeof(REVIEW_P5_SELL)                                 /* for */              \
     + (sizeof(G_swap_ctx.sell_transaction.out_currency) - 1) /* CURRENCY */         \
     + sizeof(REVIEW_P7_CONFIRM)                              /* ? */                \
     + 1)                                                     /* '\0' */

// Dynamic texts, dimensionned for worst case scenario
static char review_title_string[REVIEW_TITLE_MAX_SIZE];
static char review_confirm_string[REVIEW_CONFIRM_MAX_SIZE];

static inline void prepare_title_and_confirm(void) {
    // As the default wrapping is very ugly, we do a custom one by calculating manually
    // Detect if we should display on 2 or 3 lines.
    char delimitor_1 = ' ';
    char delimitor_2 = '\n';
    const char *p3;
    const char *p4;
    char delimitor_3 = ' ';
    const char *p5;
    const char *p6;

    // We don't always have the same title and confirm strings depending on the FLOW type
    switch (G_swap_ctx.subcommand) {
        case SWAP:
        case SWAP_NG:
            p3 = REVIEW_P3_SWAP;
            p4 = G_swap_ctx.swap_transaction.currency_from;
            p5 = REVIEW_P5_SWAP;
            p6 = G_swap_ctx.swap_transaction.currency_to;
            break;
        case SELL:
        case SELL_NG:
            p3 = REVIEW_P3_SELL;
            p4 = G_swap_ctx.sell_transaction.in_currency;
            p5 = REVIEW_P5_SELL;
            p6 = G_swap_ctx.sell_transaction.out_currency;
            break;
        case FUND:
        case FUND_NG:
            p3 = REVIEW_P3_FUND;
            p4 = "";
            p5 = REVIEW_P5_FUND;
            p6 = G_swap_ctx.fund_transaction.in_currency;
            break;
    }

#ifdef SCREEN_SIZE_WALLET
    // On Stax and Flex, try to have some fancy wrapping
    if ((G_swap_ctx.subcommand == FUND || G_swap_ctx.subcommand == FUND_NG) ||
        (strlen(p4) + strlen(p6) >= 10)) {
        PRINTF("Review title and confirm on 3 lines\n");
        // Move the "to" to the second line with the operation
        delimitor_1 = '\n';
        delimitor_2 = ' ';
        delimitor_3 = '\n';
    }
#else
    // Rely on default wrapping on Nano, not enough screen size to try to be fancy
    delimitor_1 = ' ';
    delimitor_2 = ' ';
    delimitor_3 = ' ';
#endif

    // Finally let's compute the title and confirm strings prepared above
    // Example
    // "Review transaction" + '\n' + "to" + ' ' + "swap " + "Bitcoin" + '\n' + "to " + "Ethereum"
    snprintf(review_title_string,
             sizeof(review_title_string),
             "%s%c%s%c%s%s%c%s%s",
             REVIEW_P1_TITLE,
             delimitor_1,
             REVIEW_P2,
             delimitor_2,
             p3,
             p4,
             delimitor_3,
             p5,
             p6);

#ifdef SCREEN_SIZE_WALLET
    // On Stax and Flex, display full context of the incoming operation
    snprintf(review_confirm_string,
             sizeof(review_confirm_string),
             "%s%c%s%c%s%s%c%s%s%s",
             REVIEW_P1_CONFIRM,
             delimitor_1,
             REVIEW_P2,
             delimitor_2,
             p3,
             p4,
             delimitor_3,
             p5,
             p6,
             REVIEW_P7_CONFIRM);
#else
    // On Nano, display a simple "Sign transaction to fund/swap/sell"
    snprintf(review_confirm_string,
             sizeof(review_confirm_string),
             "%s%c%s%c%s",
             REVIEW_P1_CONFIRM,
             '\n',
             REVIEW_P2,
             ' ',
             p3);
#endif
}

/**********************
 *     PAIRS LIST     *
 **********************/

static nbgl_layoutTagValue_t pairs[8];
static nbgl_layoutTagValueList_t pair_list;

static inline void prepare_pairs_list(void) {
    uint8_t index = 0;

#ifndef SCREEN_SIZE_WALLET
    // On Nano, the warning is part of the TX items. On Stax/Flex it's a warning before the tx
    if (G_swap_ctx.other_seed_payout) {
        pairs[index].item = "Warning";
        pairs[index].value = "Receive address does not belong to this Ledger device";
        index++;

        pairs[index].item = "Learn more at";
        pairs[index].value = "ledger.com/e13";
        index++;
    }
#endif

    // Prepare the values to display depending on the FLOW type
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
            pairs[index].item = "Receive estimated";
        } else {
            pairs[index].item = "Receive";
        }
        pairs[index].value = G_swap_ctx.printable_get_amount;
        index++;
    }

    pairs[index].item = "Fees";
    pairs[index].value = G_swap_ctx.printable_fees_amount;
    index++;

    if (G_swap_ctx.other_seed_payout) {
        pairs[index].item = "Receive address";
        pairs[index].value = G_swap_ctx.swap_transaction.payout_address;
        index++;
    }

    // Register the pairs we prepared into the pair list
    pair_list.nbMaxLinesForValue = 0;
    pair_list.nbPairs = index;
    pair_list.pairs = pairs;
}

/********************
 *     CALLBACK     *
 ********************/

static void handle_refusal(uint16_t error_code) {
    PRINTF("User refused transaction\n");
    reply_error(error_code);
    nbgl_useCaseReviewStatus(STATUS_TYPE_TRANSACTION_REJECTED, ui_idle);
    G_swap_ctx.state = INITIAL_STATE;
}

static void review_choice(bool confirm) {
    if (confirm) {
#ifdef SCREEN_SIZE_WALLET
        // The library application will crash if it does not overwrite the "Processing" spinner
        // started by Exchange with a UI call of it's own after being started by the os_lib_call .
        // All swappable applications currently overwrite it with the "Signing" spinner on Stax and
        // Flex and Apex devices, therefor we have no issue on these devices.
        // However, they do not all call the "Signing" spinner on NanoX and NanoSP, therefor we
        // can't safely display the "Processing" spinner until they've all been ported to the
        // latest UI guidelines.
        nbgl_useCaseSpinner("Processing");
#endif
        reply_success();
        G_swap_ctx.state = WAITING_SIGNING;
    } else {
        uint16_t error_code = USER_REFUSED_TRANSACTION;
#ifndef SCREEN_SIZE_WALLET
        // On Nano, we don't have a dedicated warning screen for cross seed swap, therefor we
        // assume all user refusals are due to involuntary cross seed swaps
        if (G_swap_ctx.other_seed_payout) {
            error_code = USER_REFUSED_CROSS_SEED;
        }
#endif
        handle_refusal(error_code);
    }
}

static void on_warning_choice(bool confirm) {
    if (confirm) {
        PRINTF("User accepted cross seed swap\n");
        nbgl_useCaseReview(TYPE_TRANSACTION,
                           &pair_list,
                           &ICON_REVIEW,
                           review_title_string,
                           NULL,
                           review_confirm_string,
                           review_choice);
    } else {
        PRINTF("User refused cross seed swap\n");
        handle_refusal(USER_REFUSED_CROSS_SEED);
    }
}

/*********************
 *    ENTRY POINT    *
 *********************/

// Only valid and used in SWAP context
void ui_validate_amounts(void) {
    prepare_title_and_confirm();
    prepare_pairs_list();

    if (G_swap_ctx.other_seed_payout) {
#ifdef SCREEN_SIZE_WALLET
        nbgl_useCaseChoice(
            &ICON_WARNING,
            "Receive address does not belong to this Ledger device",
            "Verify the swap receive address belongs to you.\nLearn more at: ledger.com/e13",
            "Continue to verify",
            "Cancel",
            on_warning_choice);
#else
        // On Nano, the warning is part of the TX items
        on_warning_choice(true);
#endif
    } else {
        on_warning_choice(true);
    }
}

#endif  // HAVE_NBGL
