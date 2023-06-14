#pragma once

#include "os.h"
#include "os_io_seproxyhal.h"
#include "states.h"
#include "commands.h"
#include "protocol.pb.h"
#include "buffer.h"
#include "swap_lib_calls.h"

#define P1_CONFIRM     0x01
#define P1_NON_CONFIRM 0x00
#define P1_FIRST       0x00
#define P1_MORE        0x80

#define CURVE_SIZE_BYTES         32U
#define UNCOMPRESSED_KEY_LENGTH  65U
#define MIN_DER_SIGNATURE_LENGTH 67U
#define MAX_DER_SIGNATURE_LENGTH 72U

#define TICKER_MIN_SIZE_B  2
#define TICKER_MAX_SIZE_B  9
#define APPNAME_MIN_SIZE_B 3

extern uint8_t G_io_seproxyhal_spi_buffer[IO_SEPROXYHAL_BUFFER_SIZE_B];

#define MIN_PARTNER_NAME_LENGHT 3
#define MAX_PARTNER_NAME_LENGHT 15

#define PARTNER_NAME_PREFIX_FOR_FUND "To "
#define PARTNER_NAME_PREFIX_SIZE     (sizeof(PARTNER_NAME_PREFIX_FOR_FUND) - 1)  // Remove trailing '\0'

#pragma pack(push, 1)
typedef struct partner_data_s {
    unsigned char name_length;
    union {
        // SELL and SWAP flows display nothing
        // FUND flow displays "To xyz"
        struct {
            char prefix[PARTNER_NAME_PREFIX_SIZE];
            char name[MAX_PARTNER_NAME_LENGHT + 1];
        };
        char prefixed_name[PARTNER_NAME_PREFIX_SIZE + MAX_PARTNER_NAME_LENGHT + 1];
    };
    cx_ecfp_256_public_key_t public_key;
} partner_data_t;
#pragma pack(pop)

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
    rate_e rate;

    // SWAP, SELL, and FUND flows are unionized as they cannot be used in the same context
    union {
        ledger_swap_NewTransactionResponse received_transaction;
        struct {
            ledger_swap_NewSellResponse sell_transaction;
            // Field not received from protobuf but needed by the application called as lib
            char sell_transaction_extra_id[1];
        };
        struct {
            ledger_swap_NewFundResponse fund_transaction;
            // Field not received from protobuf but needed by the application called as lib
            char fund_transaction_extra_id[1];
        };
    };

    unsigned char sha256_digest[32];

    cx_ecfp_256_public_key_t ledger_public_key;

    buf_t payin_coin_config;  // serialized coin configuration
    char payin_binary_name[BOLOS_APPNAME_MAX_SIZE_B + 1];

    char printable_get_amount[MAX_PRINTABLE_AMOUNT_SIZE];
    char printable_send_amount[MAX_PRINTABLE_AMOUNT_SIZE];
    char printable_fees_amount[MAX_PRINTABLE_AMOUNT_SIZE];
} swap_app_context_t;

extern swap_app_context_t G_swap_ctx;
