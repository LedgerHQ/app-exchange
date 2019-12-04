#ifndef _SWAP_APP_CONTEXT_H_
#define _SWAP_APP_CONTEXT_H_

#include "states.h"
#include "os.h"
#include "cx.h"
#include "protocol.pb.h"

typedef struct partner_data_s {
    unsigned char name_length;
    char name[15];
    cx_ecfp_256_public_key_t public_key;
} partner_data_t;

typedef struct swap_app_context_s {
    char device_tx_id[10];  // device transaction id
    partner_data_t partner;
    state_e state;
    ledger_swap_NewTransactionResponse received_transaction;
    unsigned char transaction_sha256_digest[32];
} swap_app_context_t;

#endif // _SWAP_APP_CONTEXT_H_