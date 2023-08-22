#pragma once

#include "buffer.h"

int parse_coin_config(buf_t config, buf_t *ticker, buf_t *application_name, buf_t *sub_config);
