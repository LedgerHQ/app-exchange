#ifndef _CHECKS_H_
#define _CHECKS_H_

#include <os_app.h>  // includes BOLOS_APPNAME_MAX_SIZE_B which is 32

#define TICKER_MIN_SIZE_B  2
#define TICKER_MAX_SIZE_B  9
#define APPNAME_MIN_SIZE_B 3

inline bool check_ticker_length(const buf_t* const ticker) {
    if (ticker->size < TICKER_MIN_SIZE_B || ticker->size > TICKER_MAX_SIZE_B) {
        PRINTF("Error: Ticker length should be in [%d, %d]\n",
               TICKER_MIN_SIZE_B,
               TICKER_MAX_SIZE_B);
        return false;
    }
    return true;
}

inline bool check_app_name_length(const buf_t* const application_name) {
    if (application_name->size < APPNAME_MIN_SIZE_B ||
        application_name->size > BOLOS_APPNAME_MAX_SIZE_B) {
        PRINTF("Error: Application name should be in [%d, %d]\n",
               APPNAME_MIN_SIZE_B,
               BOLOS_APPNAME_MAX_SIZE_B);
        return false;
    }
    return true;
}

#endif  // _CHECKS_H_
