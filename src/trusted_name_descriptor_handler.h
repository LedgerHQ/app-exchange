#pragma once

#include "commands.h"

int trusted_name_descriptor_handler(const command_t *cmd);

#define MAX_ADDRESS_LENGTH 44

extern uint8_t g_trusted_token_account_owner_pubkey[MAX_ADDRESS_LENGTH + 1];
extern bool g_trusted_token_account_owner_pubkey_set;