#ifndef _PARSE_CHECK_ADDRESS_MESSAGE_H_
#define _PARSE_CHECK_ADDRESS_MESSAGE_H_

#include "buffer.h"
#include "commands.h"

int parse_check_address_message(const command_t *cmd,
                                buf_t *config,
                                buf_t *der,
                                buf_t *address_parameters);

#endif
