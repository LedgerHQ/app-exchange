#pragma once

#include <os_app.h>  // includes BOLOS_APPNAME_MAX_SIZE_B which is 32

#include "globals.h"

static inline bool check_der_signature_length(const buf_t* const der) {
    if (der->size < MIN_DER_SIGNATURE_LENGTH || der->size > MAX_DER_SIGNATURE_LENGTH) {
        PRINTF("Error: DER signature length %d not in [%d, %d]\n",
               der->size,
               MIN_DER_SIGNATURE_LENGTH,
               MAX_DER_SIGNATURE_LENGTH);
        return false;
    }
    return true;
}

static inline bool check_ticker_length(const buf_t* const ticker) {
    if (ticker->size < TICKER_MIN_SIZE_B || ticker->size > TICKER_MAX_SIZE_B) {
        PRINTF("Error: Ticker length %d not in [%d, %d]\n",
               ticker->size,
               TICKER_MIN_SIZE_B,
               TICKER_MAX_SIZE_B);
        return false;
    }
    return true;
}

static inline bool check_app_name_length(const buf_t* const app_name) {
    if (app_name->size < APPNAME_MIN_SIZE_B || app_name->size > BOLOS_APPNAME_MAX_SIZE_B) {
        PRINTF("Error: Application name length %d not in [%d, %d]\n",
               app_name->size,
               APPNAME_MIN_SIZE_B,
               BOLOS_APPNAME_MAX_SIZE_B);
        return false;
    }
    return true;
}
