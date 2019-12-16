#ifndef _USER_VALIDATE_AMOUNTS_H_
#define _USER_VALIDATE_AMOUNTS_H_

int user_validate_amounts(
    char* currency_from,
    unsigned char currency_from_size,
    char* currency_to,
    unsigned char currency_to_size,
    unsigned char* amount_to_provider,
    unsigned char amount_to_provider_size,
    unsigned char* amount_to_wallet,
    unsigned char amount_to_wallet_size,
    char* partner_name,
    unsigned char partner_name_size);

#endif // _USER_VALIDATE_AMOUNTS_H_