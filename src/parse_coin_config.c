#include <string.h>
#include <os.h>

#include "parse_coin_config.h"
#include "checks.h"

typedef struct app_name_alias_s {
    const char *const foreign_name;
    const char *const app_name;
} app_name_alias_t;

const app_name_alias_t appnames_aliases[] = {
    {"Tezos", "Tezos Wallet"}  // The app name is 'Tezos Wallet' so change accordingly.
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
 *  - C the coin sub configuration, Lc its size
 */
int parse_coin_config(const buf_t *const config,
                      buf_t *ticker,
                      buf_t *application_name,
                      buf_t *sub_config) {
    uint16_t total_read = 0;
    // This function can be called with orig_buffer == configuration, so making a copy
    const buf_t input = *config;

    // Read ticker
    if (!parse_to_sized_buffer(input.bytes, input.size, ticker, &total_read)) {
        PRINTF("Cannot read the ticker\n");
        return 0;
    }
    if (!check_ticker_length(ticker)) {
        return 0;
    }

    // Read application_name
    if (!parse_to_sized_buffer(input.bytes, input.size, application_name, &total_read)) {
        PRINTF("Cannot read the application_name\n");
        return 0;
    }
    if (!check_app_name_length(application_name)) {
        return 0;
    }

    // Read sub_config
    if (!parse_to_sized_buffer(input.bytes, input.size, sub_config, &total_read)) {
        PRINTF("Cannot read the sub_config\n");
        return 0;
    }

    // Check that there is nothing else to read
    if (input.size != total_read) {
        PRINTF("Bytes to read: %d, bytes read: %d\n", input.size, total_read);
        return 0;
    }

    // Update the application name to match Ledger's naming.
    for (size_t i = 0; i < sizeof(appnames_aliases) / sizeof(appnames_aliases[0]); i++) {
        if (!strncmp((const char *) application_name->bytes,
                     (char *) (PIC(appnames_aliases[i].foreign_name)),
                     application_name->size)) {
            application_name->bytes = (unsigned char *) appnames_aliases[i].app_name;
            application_name->size = strlen((char *) PIC(appnames_aliases[i].app_name));
            break;
        }
    }

    return 1;
}
