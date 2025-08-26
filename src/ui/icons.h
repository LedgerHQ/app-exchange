#pragma once

#if defined(TARGET_NANOX) || defined(TARGET_NANOS2)
#define ICON_REVIEW  C_icon_exchange_14x14
#define ICON_WARNING C_icon_warning
#elif defined(TARGET_STAX) || defined(TARGET_FLEX)
#define ICON_REVIEW  C_icon_exchange_64x64
#define ICON_WARNING C_Warning_64px
#endif
