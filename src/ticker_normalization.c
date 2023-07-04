#include "buffer.h"
#include "globals.h"
#include "string.h"
#include "ticker_normalization.h"

typedef struct currency_alias_s {
    const char *const foreign_name;
    const char *const ledger_name;
} currency_alias_t;

const currency_alias_t currencies_aliases[] = {
    {"USDT20", "USDT"},  // Changelly's name must be changed to match the ticker from Ledger's
                         // cryptoasset list
    {"REP", "REPv2"}     // Changelly's name isn't up to date...
};

void to_uppercase(char *str, unsigned char size) {
    for (unsigned char i = 0; i < size && str[i] != 0; i++) {
        if (str[i] >= 'a' && str[i] <= 'z') {
            str[i] -= ('a' - 'A');
        }
    }
}

void set_ledger_currency_name(char *currency, size_t currency_size) {
    for (size_t i = 0; i < sizeof(currencies_aliases) / sizeof(currencies_aliases[0]); i++) {
        if (strncmp(currency,
                    (char *) (PIC(currencies_aliases[i].foreign_name)),
                    strlen((char *) PIC(currencies_aliases[i].foreign_name))) == 0) {
            strlcpy(currency, (char *) (PIC(currencies_aliases[i].ledger_name)), currency_size);
            return;
        }
    }
}

// Check if a given ticker matches the current swap context
bool check_matching_ticker(const buf_t *ticker, const char *reference_ticker) {
    char normalized_ticker_name[9];
    uint8_t normalized_ticker_len;

    // Normalize the ticker name first
    memcpy(normalized_ticker_name, ticker->bytes, sizeof(normalized_ticker_name));
    normalized_ticker_name[ticker->size] = '\0';
    to_uppercase(normalized_ticker_name, ticker->size);
    set_ledger_currency_name(normalized_ticker_name, sizeof(normalized_ticker_name));
    // Recalculate length in case it changed
    normalized_ticker_len = strlen(normalized_ticker_name);

    if (strncmp(normalized_ticker_name,
                (const char *) ticker->bytes,
                MAX(normalized_ticker_len, ticker->size)) != 0) {
        PRINTF("Normalized ticker, from '%.*s' to '%s'\n",
               ticker->size,
               ticker->bytes,
               normalized_ticker_name);
    }

    if (strlen(reference_ticker) != normalized_ticker_len ||
        strncmp(reference_ticker, normalized_ticker_name, normalized_ticker_len) != 0) {
        PRINTF("Error: Reference ticker '%.*s' doesn't match expected ticker '%.*s'\n",
               normalized_ticker_len,
               normalized_ticker_name,
               strlen(reference_ticker),
               reference_ticker);
        return false;
    }

    return true;
}
