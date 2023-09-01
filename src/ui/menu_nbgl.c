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

static const char* const info_types[] = {"Version", "Exchange App"};
static const char* const info_contents[] = {APPVERSION, "(c) 2023 Ledger"};

#define SETTINGS_PAGE_NUMBER 2
static bool nav_callback(uint8_t page, nbgl_pageContent_t* content) {
    if (page == 0) {
        content->type = INFOS_LIST;
        content->infosList.nbInfos = 2;
        content->infosList.infoTypes = info_types;
        content->infosList.infoContents = info_contents;
    } else {
        return false;
    }

    return true;
}

static void ui_menu_settings(void) {
    nbgl_useCaseSettings(APPNAME, 0, 1, false, ui_idle, nav_callback, NULL);
}

void ui_idle(void) {
    nbgl_useCaseHome(APPNAME,
                     &C_icon_exchange_64x64,
                     "This app enables swapping\nand selling assets\nin Ledger Live.",
                     true,
                     ui_menu_settings,
                     app_quit);
}

#endif  // HAVE_NBGL
