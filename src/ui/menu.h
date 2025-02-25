#pragma once

#if defined(SCREEN_SIZE_WALLET)
#define ICON_APP_WARNING    &C_Warning_64px
#define ICON_APP_EXCHANGE   &C_icon_exchange_64x64
#ifndef TEST_BUILD
#define HOME_TEXT "This app enables swapping\nand selling assets\nin Ledger Live."
#else
#define HOME_TEXT "DO NOT USE THIS APPLICATION\nWITH REAL FUNDS.\n!! TEST ONLY !!"
#endif
#else // SCREEN_SIZE_WALLET
#define ICON_APP_EXCHANGE   NULL
#define ICON_APP_WARNING    &C_icon_warning
#ifndef TEST_BUILD
#define HOME_TEXT "Exchange is ready"
#else
#define HOME_TEXT "DO NOT USE WITH REAL FUNDS"
#endif
#endif

void ui_idle(void);
