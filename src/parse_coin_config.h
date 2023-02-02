#pragma once

#include "buffer.h"

int parse_coin_config(const buf_t *const config,
                      buf_t *ticker,
                      buf_t *application_name,
                      buf_t *sub_config);
