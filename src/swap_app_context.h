#ifndef _SWAP_APP_CONTEXT_H_
#define _SWAP_APP_CONTEXT_H_

#include "states.h"
#include "os.h"
#include "protocol.pb.h"
#include "cx.h"

typedef struct partner_data_s {
    unsigned char name_length;
    char name[15];
    cx_ecfp_256_public_key_t public_key;
} partner_data_t;

typedef struct swap_app_context_s {
    unsigned char transaction_fee[16];
    unsigned char transaction_fee_length;
    union {
        char swap[10];           // device_transaction_id (SWAP)
        unsigned char sell[32];  // device_transaction_id (SELL)
    } device_transaction_id;
    partner_data_t partner;
    state_e state;
    union {
        ledger_swap_NewTransactionResponse received_transaction;  // SWAP
        ledger_swap_NewSellResponse sell_transaction;             // SELL
    };
    unsigned char sha256_digest[32];
    cx_ecfp_256_public_key_t ledger_public_key;
    unsigned char *payin_coin_config;  // serialized coin configuration
    int payin_coin_config_length;
    char payin_binary_name[16];
    char printable_get_amount[30];
} swap_app_context_t;

extern swap_app_context_t swap_ctx;

#endif  // _SWAP_APP_CONTEXT_H_
