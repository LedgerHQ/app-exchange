#pragma once

#include "commands.h"
#include "buf.h"

int check_addresses_and_amounts(const command_t *cmd);

uint16_t parse_check_address(const buf_t data,
                             buf_t *address_parameters,
                             buf_t *ticker,
                             char (*application_name)[BOLOS_APPNAME_MAX_SIZE_B + 1],
                             buf_t *sub_coin_config);
