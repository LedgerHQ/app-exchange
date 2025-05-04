#pragma once

#include "buffer.h"
#include "commands.h"

bool parse_check_address_message(buf_t data, buf_t *config, buf_t *der, buf_t *address_parameters);
