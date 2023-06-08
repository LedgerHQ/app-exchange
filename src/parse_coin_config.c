#include <string.h>
#include <os.h>

#include "parse_coin_config.h"

typedef struct app_name_alias_s {
    const char *const foreign_name;
    const char *const app_name;
} app_name_alias_t;

// The CAL is wrong on some appnames, alias them to the correct one
const app_name_alias_t appnames_aliases[] = {
    {"Tezos", "Tezos Wallet"},
    {"bsc", "Binance Smart Chain"},
    {"Bsc", "Binance Smart Chain"},
};

/*
 * Parses a configuration buffer and fills the following arguments with embedded data
 *
 * The buffer is composed of:
 *
 * | Lt | T | La | A | Lc | C |
 *
 * With:
 *  - T the ticker symbol, Lt its size
 *  - A the application name, La its size
 *  - C the configuration, Lc its size
 */
int parse_coin_config(const buf_t *const buffer,
                      buf_t *ticker,
                      buf_t *application_name,
                      buf_t *configuration) {
    // This function can be called with buffer == configuration, so making a copy
    const buf_t buffer_copy = *buffer;

    ticker->bytes = 0;
    ticker->size = 0;
    application_name->bytes = 0;
    application_name->size = 0;
    configuration->bytes = 0;
    configuration->size = 0;
    // ticker
    if (buffer_copy.size < 3) return 0;
    ticker->size = buffer_copy.bytes[0];
    if (buffer_copy.size < 3 + ticker->size) return 0;
    if (ticker->size > 0) ticker->bytes = buffer_copy.bytes + 1;
    // application_name
    application_name->size = buffer_copy.bytes[1 + ticker->size];
    if (buffer_copy.size < 3 + ticker->size + application_name->size ||
        application_name->size == 0) {
        return 0;
    }
    application_name->bytes = buffer_copy.bytes + 1 + ticker->size + 1;
    // configuration
    configuration->size = buffer_copy.bytes[1 + ticker->size + 1 + application_name->size];
    if (buffer_copy.size != 3 + ticker->size + application_name->size + configuration->size) {
        return 0;
    }
    if (configuration->size > 0) {
        configuration->bytes =
            buffer_copy.bytes + 1 + ticker->size + 1 + application_name->size + 1;
    }

    // Update the application name to match Ledger's naming.
    for (size_t i = 0; i < sizeof(appnames_aliases) / sizeof(appnames_aliases[0]); i++) {
        if (strlen((char *) PIC(appnames_aliases[i].foreign_name)) == application_name->size &&
            strncmp((const char *) application_name->bytes,
                    (char *) (PIC(appnames_aliases[i].foreign_name)),
                    application_name->size) == 0) {
            PRINTF("Aliased appname, from '%.*s'\n",
                   application_name->size,
                   application_name->bytes);
            application_name->bytes = (uint8_t *) appnames_aliases[i].app_name;
            application_name->size = strlen((char *) PIC(appnames_aliases[i].app_name));
            PRINTF("Aliased appname, to '%.*s'\n",
                   application_name->size,
                   PIC(application_name->bytes));
            break;
        }
    }

    return 1;
}
