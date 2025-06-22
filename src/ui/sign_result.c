#ifdef HAVE_NBGL

#include "globals.h"
#include "menu.h"
#include "nbgl_use_case.h"
#include "sign_result.h"

#define REFUSAL_TEXT_PART_1 "Incorrect transaction\nrejected by the\n"
#define REFUSAL_TEXT_PART_2 " app"
#define REFUSAL_TEXT_MAX_SIZE                                                         \
    ((sizeof(REFUSAL_TEXT_PART_1) - 1) + (sizeof(G_swap_ctx.payin_binary_name) - 1) + \
     (sizeof(REFUSAL_TEXT_PART_2) - 1) + 1)
static char refusal_text[REFUSAL_TEXT_MAX_SIZE];

#define EXCEPTION_TEXT_PART_1 "Exception raised\nby the\n"
#define EXCEPTION_TEXT_PART_2 " app.\nTransaction state is unknown"
#define EXCEPTION_TEXT_MAX_SIZE                                                         \
    ((sizeof(EXCEPTION_TEXT_PART_1) - 1) + (sizeof(G_swap_ctx.payin_binary_name) - 1) + \
     (sizeof(EXCEPTION_TEXT_PART_2) - 1) + 1)
static char exception_text[EXCEPTION_TEXT_MAX_SIZE];

void display_signing_failure(const char *appname) {
    snprintf(refusal_text,
             sizeof(refusal_text),
             "%s%s%s",
             REFUSAL_TEXT_PART_1,
             appname,
             REFUSAL_TEXT_PART_2);
    nbgl_useCaseStatus(refusal_text, false, ui_idle);
}

void display_signing_success(void) {
    nbgl_useCaseReviewStatus(STATUS_TYPE_TRANSACTION_SIGNED, ui_idle);
}

void display_signing_exception(const char *appname) {
    snprintf(exception_text,
             sizeof(exception_text),
             "%s%s%s",
             REFUSAL_TEXT_PART_1,
             appname,
             REFUSAL_TEXT_PART_2);
    nbgl_useCaseStatus(exception_text, false, ui_idle);
}

#endif  // HAVE_NBGL
