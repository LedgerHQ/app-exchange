#include "parse_coin_config.h"

// 1 byte - the length X of ticker
// X byte - ticker
// 1 byte - the length Y of application name
// Y byte - application name
// 1 byte - the length Z of coin configuration
// Z byte - coin configuration
int parse_coin_config(unsigned char* config, unsigned char config_length,
                      unsigned char** ticker, unsigned char* ticker_length,
                      unsigned char** application_name, unsigned char* application_name_length,
                      unsigned char** pure_config, unsigned char *pure_config_length) {
    *ticker = 0;
    *ticker_length = 0;
    *application_name = 0;
    *application_name_length = 0;
    *pure_config = 0;
    *pure_config_length = 0;
    if (config_length < 3)
        return 0;
    *ticker_length = config[0];
    if (config_length < 3 + *ticker_length)
        return 0;
    if (*ticker_length > 0)
        *ticker = config + 1;
    *application_name_length = config[1 + *ticker_length];
    if (config_length < 3 + *ticker_length + *application_name_length)
        return 0;
    if (*application_name_length > 0)
        *application_name = config + 1 + *ticker_length + 1;
    *pure_config_length = config[1 + *ticker_length + 1 + *application_name_length];
    if (config_length != 3 + *ticker_length + *application_name_length + *pure_config_length)
        return 0;
    if (*pure_config_length > 0)
        *pure_config = config + 1 + *ticker_length + 1 + *application_name_length + 1;
    return 1;
}
