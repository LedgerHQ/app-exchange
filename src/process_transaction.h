#pragma once

#include "commands.h"

void to_uppercase(char *str, unsigned char size);

void set_ledger_currency_name(char *currency, size_t currency_size);

int process_transaction(const command_t *cmd);
