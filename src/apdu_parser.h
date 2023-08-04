#pragma once

#include "commands.h"

uint16_t apdu_parser(uint8_t *apdu, size_t apdu_length, command_t *command);
