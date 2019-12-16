#include "menu.h"
#include "os.h"

static const ux_menu_entry_t menu_main[] = {
    {NULL, NULL, 0, NULL, "SWAP", "ready", 0, 0},
    {NULL, os_sched_exit, 0, &C_icon_dashboard, "Quit app", NULL, 50, 29},
    UX_MENU_END
};

void ui_idle(void) {
    UX_MENU_DISPLAY(0, menu_main, NULL);
}
