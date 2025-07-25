#ifdef HAVE_NBGL

#include "commands.h"
#include "globals.h"
#include "glyphs.h"
#include "menu.h"
#include "nbgl_use_case.h"
#include "nbgl_page.h"
#include "nbgl_layout.h"
#include "os.h"
#include "io.h"
#include "ux.h"

static void app_quit(void) {
    os_sched_exit(-1);
}

#define SETTING_INFO_NB 2
static const char* const INFO_TYPES[SETTING_INFO_NB] = {"Version", "Exchange App"};
static const char* const INFO_CONTENTS[SETTING_INFO_NB] = {APPVERSION, "(c) 2024 Ledger"};

static const nbgl_contentInfoList_t infoList = {
    .nbInfos = SETTING_INFO_NB,
    .infoTypes = INFO_TYPES,
    .infoContents = INFO_CONTENTS,
};

void ui_idle(void) {
    nbgl_useCaseHomeAndSettings(APPNAME,
#ifndef TEST_BUILD
                                &C_icon_exchange_64x64,
                                "This app enables swapping\nand selling assets\nin Ledger Live.",
#else
                                &C_Warning_64px,
                                "DO NOT USE THIS APPLICATION\nWITH REAL FUNDS.\n!! TEST ONLY !!",
#endif
                                INIT_HOME_PAGE,
                                NULL,
                                &infoList,
                                NULL,
                                app_quit);
}

#endif  // HAVE_NBGL
