#pragma once

#include "lib_standard_app/swap_lib_calls.h"
#include "buffer.h"

// return 1 if the address match, 0 is not match,
// other values in case of error
int check_address(buf_t *coin_config,
                  buf_t *address_parameters,
                  char *application_name,
                  char *address_to_check,
                  char *address_extra_id_to_check);

int get_printable_amount(buf_t *coin_config,
                         char *application_name,
                         unsigned char *amount,
                         unsigned char amount_size,
                         char *printable_amount,
                         unsigned char printable_amount_size,
                         bool is_fee);

int create_payin_transaction(create_transaction_parameters_t *params);
