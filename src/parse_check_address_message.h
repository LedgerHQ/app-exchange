#ifndef _PARSE_CHECK_ADDRESS_MESSAGE_H_
#define _PARSE_CHECK_ADDRESS_MESSAGE_H_

#include "buffer.h"

int parse_check_address_message(const buf_t *input,
                                buf_t *config,
                                buf_t *der,
                                buf_t *address_parameters);

#endif
