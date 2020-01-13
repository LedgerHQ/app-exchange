#ifndef _USER_VALIDATE_AMOUNTS_H_
#define _USER_VALIDATE_AMOUNTS_H_

#include "swap_app_context.h"
#include "send_function.h"

int user_validate_amounts(
    char* send_amount,
    char* get_amount,
    char* partner_name,
    swap_app_context_t* ctx,
    SendFunction send);

#endif // _USER_VALIDATE_AMOUNTS_H_