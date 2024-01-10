#pragma once

#include "buffer.h"

bool parse_coin_config(buf_t config, buf_t *ticker, buf_t *application_name, buf_t *sub_config);
