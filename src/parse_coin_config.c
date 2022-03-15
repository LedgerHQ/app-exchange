#include "parse_coin_config.h"
#include "string.h"
#include "os.h"

typedef struct app_name_alias_s {
    char *foreign_name;
    char *app_name;
} app_name_alias_t;

const app_name_alias_t appnames_aliases[] = {
    {"Tezos", "Tezos Wallet"}  // The app name is 'Tezos Wallet' so change accordingly.
};

void set_ledger_application_name(buf_t *application_name) {
    for (size_t i = 0; i < sizeof(appnames_aliases) / sizeof(appnames_aliases[0]); i++) {
        if (!strcmp((const char *) application_name->bytes,
                    (char *) (PIC(appnames_aliases[i].foreign_name)))) {
            // Copy the correct application name.
            strcpy((char *) application_name->bytes, (char *) (PIC(appnames_aliases[i].app_name)));
            // Update the application name size accordingly.
            application_name->size = strlen((char *) PIC(appnames_aliases[i].app_name));
            return;
        }
    }
}

// 1 byte - the length X of ticker
// X byte - ticker
// 1 byte - the length Y of application name
// Y byte - application name
// 1 byte - the length Z of coin configuration
// Z byte - coin configuration
int parse_coin_config(buf_t *config_, buf_t *ticker, buf_t *application_name, buf_t *pure_config) {
    // This function is sometimes called with config_ == pure_config, make a
    // copy.
    buf_t config = *config_;

    ticker->bytes = 0;
    ticker->size = 0;
    application_name->bytes = 0;
    application_name->size = 0;
    pure_config->bytes = 0;
    pure_config->size = 0;
    if (config.size < 3) return 0;
    ticker->size = config.bytes[0];
    if (config.size < 3 + ticker->size) return 0;
    if (ticker->size > 0) ticker->bytes = config.bytes + 1;
    application_name->size = config.bytes[1 + ticker->size];
    if (config.size < 3 + ticker->size + application_name->size) return 0;
    if (application_name->size > 0) application_name->bytes = config.bytes + 1 + ticker->size + 1;
    pure_config->size = config.bytes[1 + ticker->size + 1 + application_name->size];
    if (config.size != 3 + ticker->size + application_name->size + pure_config->size) return 0;
    if (pure_config->size > 0)
        pure_config->bytes = config.bytes + 1 + ticker->size + 1 + application_name->size + 1;

    // Update the application name to match Ledger's naming.
    set_ledger_application_name(application_name);

    return 1;
}
