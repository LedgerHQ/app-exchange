#include <string.h>
#include <os.h>

#include "parse_coin_config.h"

typedef struct app_name_alias_s {
    const char *const foreign_name;
    const char *const app_name;
} app_name_alias_t;

const app_name_alias_t appnames_aliases[] = {
    {"Tezos", "Tezos Wallet"}  // The app name is 'Tezos Wallet' so change accordingly.
};

// 1 byte  - the length X of ticker
// X bytes - ticker
// 1 byte  - the length Y of application name
// Y bytes - application name
// 1 byte  - the length Z of coin configuration
// Z bytes - coin configuration
int parse_coin_config(const buf_t *const config_,
                      buf_t *ticker,
                      buf_t *application_name,
                      buf_t *pure_config) {
    // This function can be called with config_ == pure_config, so making a copy
    const buf_t config = *config_;

    ticker->bytes = 0;
    ticker->size = 0;
    application_name->bytes = 0;
    application_name->size = 0;
    pure_config->bytes = 0;
    pure_config->size = 0;
    // ticker
    if (config.size < 3) return 0;
    ticker->size = config.bytes[0];
    if (config.size < 3 + ticker->size) return 0;
    if (ticker->size > 0) ticker->bytes = config.bytes + 1;
    // application_name
    application_name->size = config.bytes[1 + ticker->size];
    if (config.size < 3 + ticker->size + application_name->size || application_name->size == 0) {
        return 0;
    }
    application_name->bytes = config.bytes + 1 + ticker->size + 1;
    // pure_config
    pure_config->size = config.bytes[1 + ticker->size + 1 + application_name->size];
    if (config.size != 3 + ticker->size + application_name->size + pure_config->size) return 0;
    if (pure_config->size > 0)
        pure_config->bytes = config.bytes + 1 + ticker->size + 1 + application_name->size + 1;

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
