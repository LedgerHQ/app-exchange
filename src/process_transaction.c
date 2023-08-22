#include <cx.h>

#include "process_transaction.h"
#include "pb_decode.h"
#include "proto/protocol.pb.h"
#include "swap_errors.h"
#include "io.h"
#include "base64.h"
#include "pb_structs.h"
#include "globals.h"
#include "ticker_normalization.h"

/*
 * Trims leading 0s on `PB_BYTES_ARRAY_T.bytes` fields.
 *
 * This field is to be sent 'as is' to coin application to inform them of
 * sending/getting coins. Some applications expect a small field (i.e: Bitcoin
 * needs 8B max).
 * This function only trims the leading 0s as much as possible, meaning if the
 * field value does overflow, the coin application would return an error.
 *
 * The operation should be valid for any kind of PB_BYTES_ARRAY_T, but is
 * currently restricted to PB_BYTES_ARRAY_T(16) (pb_bytes_array_16_t) for
 * type consistency.
 */

static void trim_pb_bytes_array(pb_bytes_array_16_t *transaction) {
    pb_size_t i;
    for (i = 0; i < transaction->size; i++) {
        if (transaction->bytes[i] != 0) {
            break;
        }
    }
    if (i == 0) {
        return;
    }
    transaction->size -= i;
    memmove(transaction->bytes, transaction->bytes + i, transaction->size);
}

static bool parse_transaction(uint8_t *in,
                              size_t in_size,
                              subcommand_e subcommand,
                              buf_t *payload,
                              buf_t *fees) {
    // On legacy flows the length field is 1 byte
    uint8_t payload_length_field_size = 2;
    if (subcommand == SWAP || subcommand == SELL || subcommand == FUND) {
        payload_length_field_size = 1;
    }

    uint16_t offset = 0;
    if (!parse_to_sized_buffer(in, in_size, payload_length_field_size, payload, &offset)) {
        PRINTF("Failed to parse payload\n");
        return false;
    }

    if (!parse_to_sized_buffer(in, in_size, 1, fees, &offset)) {
        PRINTF("Failed to parse fees\n");
        return false;
    }

    if (offset != in_size) {
        PRINTF("Leftover data to read, received %d bytes, read %d bytes\n", in_size, offset);
        return false;
    }

    if (fees->size > sizeof(G_swap_ctx.transaction_fee)) {
        PRINTF("Error: Transaction fee buffer is too long, received %d, max is %d\n",
               fees->size,
               sizeof(G_swap_ctx.transaction_fee));
        return false;
    }

    return true;
}

static bool calculate_sha256_digest(buf_t payload, subcommand_e subcommand) {
    cx_sha256_t sha256;

    cx_sha256_init(&sha256);

    if (subcommand != SWAP) {
        unsigned char dot = '.';
        if (cx_hash_no_throw(&sha256.header, 0, &dot, 1, NULL, 0) != CX_OK) {
            PRINTF("Error: cx_hash_no_throw\n");
            return false;
        }
    }

    if (cx_hash_no_throw(&sha256.header,
                         CX_LAST,
                         payload.bytes,
                         payload.size,
                         G_swap_ctx.sha256_digest,
                         sizeof(G_swap_ctx.sha256_digest)) != CX_OK) {
        PRINTF("Error: cx_hash_no_throw\n");
        return false;
    }

    PRINTF("sha256_digest: %.*H\n", 32, G_swap_ctx.sha256_digest);

    return true;
}

static bool deserialize_protobuf_payload(buf_t payload, subcommand_e subcommand) {
    pb_istream_t stream;
    const pb_field_t *fields;
    void *dest_struct;

    // Temporary buffer if the received payload is encoded. Size is arbitrary
    unsigned char decoded[256];

    buf_t to_deserialize;

    if (subcommand != SWAP) {
        int n = base64_decode(decoded,
                              sizeof(decoded),
                              (const unsigned char *) payload.bytes,
                              payload.size);
        if (n < 0) {
            PRINTF("Error: Can't decode SELL/FUND/NG transaction base64\n");
            return false;
        }
        to_deserialize.bytes = decoded;
        to_deserialize.size = n;
    } else {
        to_deserialize = payload;
    }

    stream = pb_istream_from_buffer(to_deserialize.bytes, to_deserialize.size);

    if (subcommand == SWAP || subcommand == SWAP_NG) {
        fields = ledger_swap_NewTransactionResponse_fields;
        dest_struct = &G_swap_ctx.received_transaction;
    } else if (subcommand == SELL || subcommand == SELL_NG) {
        fields = ledger_swap_NewSellResponse_fields;
        dest_struct = &G_swap_ctx.sell_transaction;
    } else {
        fields = ledger_swap_NewFundResponse_fields;
        dest_struct = &G_swap_ctx.fund_transaction;
    }

    if (!pb_decode(&stream, fields, dest_struct)) {
        PRINTF("Error: Can't deserialize protobuf payload\n");
        return false;
    }

    // Field not received from protobuf
    if (subcommand == SELL || subcommand == SELL_NG) {
        G_swap_ctx.sell_transaction_extra_id[0] = '\0';
    } else if (subcommand == FUND || subcommand == FUND_NG) {
        G_swap_ctx.fund_transaction_extra_id[0] = '\0';
    }

    return true;
}

static bool check_transaction_id(subcommand_e subcommand) {
    if (subcommand == SWAP) {
        if (memcmp(G_swap_ctx.device_transaction_id.swap,
                   G_swap_ctx.received_transaction.device_transaction_id,
                   sizeof(G_swap_ctx.device_transaction_id.swap)) != 0) {
            PRINTF("Error: Device transaction IDs don't match, expected %.*H, received %.*H\n",
                   sizeof(G_swap_ctx.device_transaction_id.swap),
                   G_swap_ctx.device_transaction_id.swap,
                   sizeof(G_swap_ctx.device_transaction_id.swap),
                   G_swap_ctx.received_transaction.device_transaction_id);
            return false;
        }
    } else {
        pb_bytes_array_32_t *tx_id;
        if (subcommand == SELL || subcommand == SELL_NG) {
            tx_id = (pb_bytes_array_32_t *) &G_swap_ctx.sell_transaction.device_transaction_id;
        } else if (subcommand == FUND || subcommand == FUND_NG) {
            tx_id = (pb_bytes_array_32_t *) &G_swap_ctx.fund_transaction.device_transaction_id;
        } else {
            tx_id =
                (pb_bytes_array_32_t *) &G_swap_ctx.received_transaction.device_transaction_id_ng;
        }

        if (tx_id->size != sizeof(G_swap_ctx.device_transaction_id.sell_fund)) {
            PRINTF("Error: Device transaction ID size doesn't match, exp %d bytes, recv %d bytes\n",
                   sizeof(G_swap_ctx.device_transaction_id.sell_fund),
                   tx_id->size);
            return false;
        }
        if (memcmp(G_swap_ctx.device_transaction_id.sell_fund, tx_id->bytes, tx_id->size) != 0) {
            PRINTF("Error: Device transaction IDs don't match, expected %.*H, received %.*H\n",
                   tx_id->size,
                   tx_id->bytes,
                   sizeof(G_swap_ctx.device_transaction_id.sell_fund),
                   G_swap_ctx.device_transaction_id.sell_fund);
            return false;
        }
    }

    return true;
}

static void normalize_currencies(subcommand) {
    if (subcommand == SWAP || subcommand == SWAP_NG) {
        to_uppercase(G_swap_ctx.received_transaction.currency_from,
                     sizeof(G_swap_ctx.received_transaction.currency_from));
        set_ledger_currency_name(G_swap_ctx.received_transaction.currency_from,
                                 sizeof(G_swap_ctx.received_transaction.currency_from) /
                                     sizeof(G_swap_ctx.received_transaction.currency_from[0]));

        to_uppercase(G_swap_ctx.received_transaction.currency_to,
                     sizeof(G_swap_ctx.received_transaction.currency_to));
        set_ledger_currency_name(G_swap_ctx.received_transaction.currency_to,
                                 sizeof(G_swap_ctx.received_transaction.currency_to) /
                                     sizeof(G_swap_ctx.received_transaction.currency_to[0]));

        // strip bcash CashAddr header, and other bicmd->subcommand1 like headers
        for (size_t i = 0; i < sizeof(G_swap_ctx.received_transaction.payin_address); i++) {
            if (G_swap_ctx.received_transaction.payin_address[i] == ':') {
                memmove(G_swap_ctx.received_transaction.payin_address,
                        G_swap_ctx.received_transaction.payin_address + i + 1,
                        sizeof(G_swap_ctx.received_transaction.payin_address) - i - 1);
                break;
            }
        }
    } else if (subcommand == SELL || subcommand == SELL_NG) {
        to_uppercase(G_swap_ctx.sell_transaction.in_currency,
                     sizeof(G_swap_ctx.sell_transaction.in_currency));
        set_ledger_currency_name(G_swap_ctx.sell_transaction.in_currency,
                                 sizeof(G_swap_ctx.sell_transaction.in_currency) /
                                     sizeof(G_swap_ctx.sell_transaction.in_currency[0]));
    } else if (subcommand == FUND || subcommand == FUND_NG) {
        to_uppercase(G_swap_ctx.fund_transaction.in_currency,
                     sizeof(G_swap_ctx.fund_transaction.in_currency));
        set_ledger_currency_name(G_swap_ctx.fund_transaction.in_currency,
                                 sizeof(G_swap_ctx.fund_transaction.in_currency) /
                                     sizeof(G_swap_ctx.fund_transaction.in_currency[0]));
    }
}

// triming leading 0s
static void trim_amounts(subcommand) {
    if (subcommand == SWAP || subcommand == SWAP_NG) {
        trim_pb_bytes_array(
            (pb_bytes_array_16_t *) &G_swap_ctx.received_transaction.amount_to_provider);
        trim_pb_bytes_array(
            (pb_bytes_array_16_t *) &G_swap_ctx.received_transaction.amount_to_wallet);
    } else if (subcommand == SELL || subcommand == SELL_NG) {
        trim_pb_bytes_array((pb_bytes_array_16_t *) &G_swap_ctx.sell_transaction.in_amount);
    } else if (subcommand == FUND || subcommand == FUND_NG) {
        trim_pb_bytes_array((pb_bytes_array_16_t *) &G_swap_ctx.fund_transaction.in_amount);
    }
}

// Extract the fees from the apdus and store them in the global context
static void save_fees(buf_t fees) {
    G_swap_ctx.transaction_fee_length = fees.size;
    memset(G_swap_ctx.transaction_fee, 0, sizeof(G_swap_ctx.transaction_fee));
    memcpy(G_swap_ctx.transaction_fee, fees.bytes, G_swap_ctx.transaction_fee_length);
    PRINTF("Transaction fees BE = %.*H\n",
           G_swap_ctx.transaction_fee_length,
           G_swap_ctx.transaction_fee);
}

int process_transaction(const command_t *cmd) {
    uint8_t undecoded_transaction[sizeof(G_swap_ctx.raw_transaction)];
    uint8_t *data;
    // For memory optimization, the undecoded protobuf apdu may have been stored in an union
    // with the decoded protobuf transaction.
    if (cmd->data.bytes == G_swap_ctx.raw_transaction) {
        // Copy locally the apdu to avoid problems during protobuf decode and fees extraction
        PRINTF("Copying locally, the APDU has been received split\n");
        memcpy(undecoded_transaction, G_swap_ctx.raw_transaction, cmd->data.size);
        data = undecoded_transaction;
    } else {
        data = cmd->data.bytes;
    }

    buf_t fees;
    buf_t payload;
    if (!parse_transaction(data, cmd->data.size, cmd->subcommand, &payload, &fees)) {
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    if (!calculate_sha256_digest(payload, cmd->subcommand)) {
        return reply_error(INTERNAL_ERROR);
    }

    if (!deserialize_protobuf_payload(payload, cmd->subcommand)) {
        return reply_error(DESERIALIZATION_FAILED);
    }

    if (!check_transaction_id(cmd->subcommand)) {
        return reply_error(WRONG_TRANSACTION_ID);
    }

    normalize_currencies(cmd->subcommand);

    trim_amounts(cmd->subcommand);

    save_fees(fees);

    if (reply_success() < 0) {
        PRINTF("Error: failed to send response\n");
        return -1;
    }

    G_swap_ctx.state = TRANSACTION_RECEIVED;

    return 0;
}
