#pragma once

#include "buf.h"

// CLA to use when communicating with Exchange
#define CLA 0xE0

// commands
typedef enum {
    GET_VERSION_COMMAND = 0x02,
    START_NEW_TRANSACTION_COMMAND = 0x03,
    SET_PARTNER_KEY_COMMAND = 0x04,
    CHECK_PARTNER_COMMAND = 0x05,
    PROCESS_TRANSACTION_RESPONSE_COMMAND = 0x06,
    CHECK_TRANSACTION_SIGNATURE_COMMAND = 0x07,
    GET_CHALLENGE = 0x10,
    SEND_TRUSTED_NAME_DESCRIPTOR = 0x11,
    CHECK_PAYOUT_ADDRESS = 0x08,
    CHECK_ASSET_IN_LEGACY_AND_DISPLAY = 0x08,  // Same ID as CHECK_PAYOUT_ADDRESS, deprecated
    CHECK_ASSET_IN_AND_DISPLAY = 0x0B,         // Do note the 0x0B
    CHECK_ASSET_IN_NO_DISPLAY = 0x0D,          // Do note the 0x0B
    CHECK_REFUND_ADDRESS_AND_DISPLAY = 0x09,
    CHECK_REFUND_ADDRESS_NO_DISPLAY = 0x0C,
    PROMPT_UI_DISPLAY = 0x0F,
    START_SIGNING_TRANSACTION = 0x0A,
} command_e;

// Different rates possible for the transaction. They are given to the app as P1 of an APDU
typedef enum {
    FIXED = 0x00,
    FLOATING = 0x01,
} rate_e;

// Different flows possible. They are given to the app as the P2 of an APDU
typedef enum {
    SWAP = 0x00,
    SELL = 0x01,
    FUND = 0x02,
    SWAP_NG = 0x03,
    SELL_NG = 0x04,
    FUND_NG = 0x05,
} subcommand_e;
// As P2 can hold more information, we use a mask to access the subcommand part of P2
#define SUBCOMMAND_MASK 0x0F

// Extension values to signal that an APDU is split
// Only supported for new unified flows during PROCESS_TRANSACTION_RESPONSE_COMMAND
#define P2_NONE (0x00 << 4)
// P2_EXTEND is set to signal that this APDU buffer extends a previous one
#define P2_EXTEND (0x01 << 4)
// P2_MORE is set to signal that this APDU buffer is not complete
#define P2_MORE (0x02 << 4)
// As P2 can hold more information, we use a mask to access the extension part of P2
#define EXTENSION_MASK 0xF0

/**
 * Structure with fields of APDU command.
 */
typedef struct {
    command_e ins;            // Instruction code
    rate_e rate;              // P1
    subcommand_e subcommand;  // P2, we don't care for the extension here as this structure is for
                              //     command handling, not apdu reception
    buf_t data;               // Command data
} command_t;
