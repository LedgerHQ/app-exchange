#ifndef _PARSE_COIN_CONFIG_H_
#define _PARSE_COIN_CONFIG_H_

#include "buffer.h"

int parse_coin_config(const buf_t *const config,
                      buf_t *ticker,
                      buf_t *application_name,
                      buf_t *pure_config);

#endif  // _PARSE_COIN_CONFIG_H_
