#ifndef _SWAP_APP_CONTEXT_H_
#define _SWAP_APP_CONTEXT_H_

#include <swap_lib_calls.h>

#include "states.h"
#include "proto/protocol.pb.h"
#include "commands.h"
#include "globals.h"
#include "buffer.h"

typedef struct partner_data_s {
    unsigned char name_length;
    char name[15];
    cx_ecfp_256_public_key_t public_key;
} partner_data_t;

typedef struct swap_app_context_s {
    union {
        unsigned char sell_fund[32];  // device_transaction_id (SELL && FUND)
        char swap[10];                // device_transaction_id (SWAP)
    } device_transaction_id;

    unsigned char transaction_fee[16];
    unsigned char transaction_fee_length;

    partner_data_t partner;
    state_e state;
    subcommand_e subcommand;

    union {
        ledger_swap_NewTransactionResponse received_transaction;  // SWAP
        ledger_swap_NewSellResponse sell_transaction;             // SELL
        ledger_swap_NewFundResponse fund_transaction;             // FUND
    };

    unsigned char sha256_digest[32];

    cx_ecfp_256_public_key_t ledger_public_key;

    buf_t payin_coin_config;  // serialized coin configuration
    char payin_binary_name[BOLOS_APPNAME_MAX_SIZE_B + 1];

    char printable_get_amount[MAX_PRINTABLE_AMOUNT_SIZE];
} swap_app_context_t;

extern swap_app_context_t swap_ctx;

#endif  // _SWAP_APP_CONTEXT_H_
