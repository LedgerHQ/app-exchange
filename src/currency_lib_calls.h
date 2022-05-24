#ifndef _SOURCE_CURRENCY_LIB_CALLS_H_
#define _SOURCE_CURRENCY_LIB_CALLS_H_

#include "swap_lib_calls.h"
#include "buffer.h"

// return 1 if the address match, 0 is not match,
// other values in case of error
int check_address(buf_t *coin_config,
                  buf_t *address_parameters,
                  char *application_name,
                  char *address_to_check,
                  char *address_extra_id_to_check);

void create_payin_transaction(char *application_name, create_transaction_parameters_t *params);

int get_printable_amount(const buf_t *const coin_config,
                         const char *const application_name,
                         const unsigned char *const amount,
                         const unsigned char amount_size,
                         char *const printable_amount,
                         const unsigned char printable_amount_size,
                         const bool is_fee);

#endif  // _SOURCE_CURRENCY_LIB_CALLS_H_
