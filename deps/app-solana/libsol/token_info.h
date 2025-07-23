#pragma once

#include "sol/parser.h"

typedef struct TokenInfo {
    Pubkey mint_address;
    char symbol[10];
} TokenInfo;

extern TokenInfo const TOKEN_REGISTRY[];

const char *get_hardcoded_token_symbol(const uint8_t *mint_address);
