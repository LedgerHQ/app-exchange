#pragma once

#include "commands.h"

uint16_t check_apdu_validity(uint8_t *apdu, size_t apdu_length, command_t *command);
