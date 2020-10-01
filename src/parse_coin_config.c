#include "parse_coin_config.h"

// 1 byte - the length X of ticker
// X byte - ticker
// 1 byte - the length Y of application name
// Y byte - application name
// 1 byte - the length Z of coin configuration
// Z byte - coin configuration
int parse_coin_config(buf_t *config_,
                      buf_t *ticker,
                      buf_t *application_name,
                      buf_t *pure_config) {
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
    if (config.size != 3 + ticker->size + application_name->size + pure_config->size)
        return 0;
    if (pure_config->size > 0)
        pure_config->bytes = config.bytes + 1 + ticker->size + 1 + application_name->size + 1;
    return 1;
}
