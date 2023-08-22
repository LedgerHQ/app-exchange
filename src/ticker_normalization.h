#pragma once

void to_uppercase(char *str, unsigned char size);

void set_ledger_currency_name(char *currency, size_t currency_size);

bool check_matching_ticker(buf_t ticker, const char *reference_ticker);
