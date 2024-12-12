#pragma once

#include "os.h"
#include "os_io_seproxyhal.h"
#include "states.h"
#include "commands.h"
#include "protocol.pb.h"
#include "buffer.h"
#include "lib_standard_app/swap_lib_calls.h"

#define CURVE_SIZE_BYTES         32U
#define UNCOMPRESSED_KEY_LENGTH  65U
#define MIN_DER_SIGNATURE_LENGTH 67U
#define MAX_DER_SIGNATURE_LENGTH 73U

#define CURVE_SECP256K1 0x00
#define CURVE_SECP256R1 0x01

#define ENCODING_BYTES_ARRAY 0x00
#define ENCODING_BASE_64_URL 0x01

#define DER_FORMAT_SIGNATURE 0x00
#define R_S_FORMAT_SIGNATURE 0x01

#define SIGNATURE_COMPUTED_ON_TX              0x00
#define SIGNATURE_COMPUTED_ON_DOT_PREFIXED_TX 0x01

#define TICKER_MIN_SIZE_B  2
#define TICKER_MAX_SIZE_B  9
#define APPNAME_MIN_SIZE_B 3

#define MAX_COIN_SUB_CONFIG_SIZE 64

extern uint8_t G_io_seproxyhal_spi_buffer[IO_SEPROXYHAL_BUFFER_SIZE_B];

#define MIN_PARTNER_NAME_LENGHT 3
#define MAX_PARTNER_NAME_LENGHT 15

#define PARTNER_NAME_PREFIX_FOR_FUND "To "

typedef struct partner_data_s {
    union {
        char unprefixed_name[MAX_PARTNER_NAME_LENGHT + 1];
        char prefixed_name[sizeof(PARTNER_NAME_PREFIX_FOR_FUND) - 1 + MAX_PARTNER_NAME_LENGHT + 1];
    };
    cx_ecfp_256_public_key_t public_key;
} partner_data_t;

typedef struct swap_app_context_s {
    union {
        uint8_t unified[32];  // device_transaction_id (SELL && FUND && NG)
        char swap[10];        // device_transaction_id (SWAP)
    } device_transaction_id;

    uint8_t transaction_fee[16];
    uint8_t transaction_fee_length;

    partner_data_t partner;
    state_e state;
    subcommand_e subcommand;
    rate_e rate;

    // SWAP, SELL, and FUND flows are unionized as they cannot be used in the same context
    union {
        // This is the raw received APDU
        uint8_t raw_transaction[256 * 2];
        ledger_swap_NewTransactionResponse swap_transaction;
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

    // During TX reception, we don't know if we'll receive the signature of the (TX), or the
    // signature of the ('.' + TX).
    // Storing the whole TX to calculate the hash during signature checking would use too much
    // stack, so we calculate the two hashes and we'll decide later which one to use.
    uint8_t sha256_digest_prefixed[32];
    uint8_t sha256_digest_no_prefix[32];

    cx_ecfp_256_public_key_t ledger_public_key;

    uint8_t paying_sub_coin_config_size;
    uint8_t paying_sub_coin_config[MAX_COIN_SUB_CONFIG_SIZE];
    char payin_binary_name[BOLOS_APPNAME_MAX_SIZE_B + 1];

    union {
        // Amount we will gain, either in crypto (SWAP) or FIAT (SELL)
        char printable_get_amount[MAX_PRINTABLE_AMOUNT_SIZE];
        // Amount name to fund
        char account_name[MAX_PRINTABLE_AMOUNT_SIZE];
    };
    char printable_send_amount[MAX_PRINTABLE_AMOUNT_SIZE];
    char printable_fees_amount[MAX_PRINTABLE_AMOUNT_SIZE];
} swap_app_context_t;

extern swap_app_context_t G_swap_ctx;

#ifdef HAVE_NBGL

// Boolean like status + a special value
typedef enum last_cycle_status_e {
    LAST_CYCLE_ERROR = 0,
    LAST_CYCLE_SUCCESS = 1,
    LAST_CYCLE_EXCEPTION = 2,
} last_cycle_status_t;

// On Stax, remember some data from the previous cycle if applicable to display a status screen
typedef struct previous_cycle_data_s {
    bool had_previous_cycle;
    last_cycle_status_t was_successful;
    char appname_last_cycle[BOLOS_APPNAME_MAX_SIZE_B + 1];
} previous_cycle_data_t;

extern previous_cycle_data_t G_previous_cycle_data;
#endif
