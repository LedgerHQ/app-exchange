#include <string.h>
#include <os.h>

#include "parse_coin_config.h"
#include "checks.h"

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
 *  - C the sub configuration, Lc its size
 *
 * As the sub configuration is optional, we accept Lc == 0
 */
bool parse_coin_config(buf_t input,
                       buf_t *ticker,
                       buf_t *application_name,
                       buf_t *sub_configuration) {
    uint16_t total_read = 0;

    // Read ticker
    if (!parse_to_sized_buffer(input.bytes, input.size, 1, ticker, &total_read)) {
        PRINTF("Cannot read the ticker\n");
        return false;
    }
    if (!check_ticker_length(ticker)) {
        return false;
    }

    // Read application_name
    if (!parse_to_sized_buffer(input.bytes, input.size, 1, application_name, &total_read)) {
        PRINTF("Cannot read the application_name\n");
        return false;
    }
    if (!check_app_name_length(application_name)) {
        return false;
    }

    // Read sub configuration
    if (!parse_to_sized_buffer(input.bytes, input.size, 1, sub_configuration, &total_read)) {
        PRINTF("Cannot read the sub_configuration\n");
        return false;
    }
    if (sub_configuration->size > MAX_COIN_SUB_CONFIG_SIZE) {
        PRINTF("Sub coin sub_configuration size %d is too big\n", sub_configuration->size);
        return false;
    }

    // Check that there is nothing else to read
    if (input.size != total_read) {
        PRINTF("Bytes to read: %d, bytes read: %d\n", input.size, total_read);
        return false;
    }

    // Update the application name to match Ledger's naming.
    for (size_t i = 0; i < sizeof(appnames_aliases) / sizeof(appnames_aliases[0]); i++) {
        if (strlen((char *) PIC(appnames_aliases[i].foreign_name)) == application_name->size &&
            strncmp((const char *) application_name->bytes,
                    (char *) (PIC(appnames_aliases[i].foreign_name)),
                    application_name->size) == 0) {
            PRINTF("Aliased from '%.*s'\n", application_name->size, application_name->bytes);
            application_name->bytes = (uint8_t *) PIC(appnames_aliases[i].app_name);
            application_name->size = strlen((char *) application_name->bytes);
            PRINTF("to '%.*s'\n", application_name->size, application_name->bytes);
            break;
        }
    }

    return true;
}
