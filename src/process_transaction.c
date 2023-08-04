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

static void normalize_currencies(void) {
    to_uppercase(G_swap_ctx.received_transaction.currency_from,
                 sizeof(G_swap_ctx.received_transaction.currency_from));
    to_uppercase(G_swap_ctx.received_transaction.currency_to,
                 sizeof(G_swap_ctx.received_transaction.currency_to));
    set_ledger_currency_name(G_swap_ctx.received_transaction.currency_from,
                             sizeof(G_swap_ctx.received_transaction.currency_from) /
                                 sizeof(G_swap_ctx.received_transaction.currency_from[0]));
    set_ledger_currency_name(G_swap_ctx.received_transaction.currency_to,
                             sizeof(G_swap_ctx.received_transaction.currency_to) /
                                 sizeof(G_swap_ctx.received_transaction.currency_to[0]));
    // triming leading 0s
    trim_pb_bytes_array(
        (pb_bytes_array_16_t *) &(G_swap_ctx.received_transaction.amount_to_provider));
    trim_pb_bytes_array(
        (pb_bytes_array_16_t *) &(G_swap_ctx.received_transaction.amount_to_wallet));

    // strip bcash CashAddr header, and other bicmd->subcommand1 like headers
    for (size_t i = 0; i < sizeof(G_swap_ctx.received_transaction.payin_address); i++) {
        if (G_swap_ctx.received_transaction.payin_address[i] == ':') {
            memmove(G_swap_ctx.received_transaction.payin_address,
                    G_swap_ctx.received_transaction.payin_address + i + 1,
                    sizeof(G_swap_ctx.received_transaction.payin_address) - i - 1);
            break;
        }
    }
}

int process_transaction(const command_t *cmd) {
    PRINTF("cmd->data.size = %d\n", cmd->data.size);
    for (int i = 0; i < cmd->data.size; ++i) {
        PRINTF("%02x", cmd->data.bytes[i]);
    }
    PRINTF("\n");
    if (cmd->data.size < 2) {
        PRINTF("Error: Can't parse process_transaction message, length should be more than 2\n");

        return reply_error(DESERIALIZATION_FAILED);
    }

    uint8_t *data;
    uint8_t undecoded_transaction[sizeof(G_swap_ctx.raw_transaction)];
    if (cmd->data.bytes == G_swap_ctx.raw_transaction) {
        PRINTF("Copying locally, the APDU has been received split\n");
        // For memory optimization, the undecded protobuf apdu may have been stored in an union with the decoded apdus
        // Copy locally to avoid problems during protobuf decode
        memcpy(undecoded_transaction, G_swap_ctx.raw_transaction, cmd->data.size);
        PRINTF("cmd->data.size = %d\n", cmd->data.size);
        for (int i = 0; i < cmd->data.size; ++i) {
            PRINTF("%02x", undecoded_transaction[i]);
        }
        PRINTF("\n");
        data = undecoded_transaction;
    } else {
        data = cmd->data.bytes;
    }

    uint16_t payload_length;
    uint8_t data_offset;
    if (cmd->subcommand == SWAP_NG) {
        data_offset = 2;
        payload_length = U2BE(data, 0);
    } else {
        data_offset = 1;
        payload_length = data[0];
    }
    if (cmd->data.size < data_offset + payload_length) {
        PRINTF("Error: Can't parse process_transaction message, invalid payload length\n");
        return reply_error(DESERIALIZATION_FAILED);
    }
    data += data_offset;

    pb_istream_t stream;
    cx_sha256_t sha256;

    cx_sha256_init(&sha256);

    PRINTF("len(payload) = %d\n", payload_length);
    for (int i = 0; i < payload_length; ++i) {
        PRINTF("%02x", data[i]);
    }
    PRINTF("\n");

    if (cmd->subcommand == SWAP) {
        PRINTF("payload_length = %d\n", payload_length);
        for (int i = 0; i < payload_length; ++i) {
            PRINTF("%02x", data[i]);
        }
        PRINTF("\n");
        if (cx_hash_no_throw(&sha256.header,
                             CX_LAST,
                             data,
                             payload_length,
                             G_swap_ctx.sha256_digest,
                             sizeof(G_swap_ctx.sha256_digest)) != CX_OK) {
            PRINTF("Error: cx_hash_no_throw\n");
            return reply_error(INTERNAL_ERROR);
        }

        PRINTF("sha256_digest: %.*H\n", 32, G_swap_ctx.sha256_digest);

        stream = pb_istream_from_buffer(data, payload_length);

        if (!pb_decode(&stream,
                       ledger_swap_NewTransactionResponse_fields,
                       &G_swap_ctx.received_transaction)) {
            PRINTF("Error: Can't parse SWAP transaction protobuf\n%.*H\n",
                   payload_length,
                   data);

            return reply_error(DESERIALIZATION_FAILED);
        }

        if (memcmp(G_swap_ctx.device_transaction_id.swap,
                   G_swap_ctx.received_transaction.device_transaction_id,
                   sizeof(G_swap_ctx.device_transaction_id.swap)) != 0) {
            PRINTF(
                "Error: Device transaction IDs (SWAP) doesn't match. Expected: {%.*H}, got "
                "{%.*H}\n",
                sizeof(G_swap_ctx.device_transaction_id.swap),
                G_swap_ctx.device_transaction_id.swap,
                sizeof(G_swap_ctx.device_transaction_id.swap),
                G_swap_ctx.received_transaction.device_transaction_id);

            return reply_error(WRONG_TRANSACTION_ID);
        }

        normalize_currencies();
    }

    if (cmd->subcommand == SELL || cmd->subcommand == FUND || cmd->subcommand == SWAP_NG || cmd->subcommand == SELL_NG || cmd->subcommand == FUND_NG) {
        // arbitrary maximum payload size
        unsigned char payload[256];


        unsigned char dot = '.';

        if (cx_hash_no_throw(&sha256.header, 0, &dot, 1, NULL, 0) != CX_OK) {
            PRINTF("Error: cx_hash_no_throw\n");
            return reply_error(INTERNAL_ERROR);
        }
        if (cx_hash_no_throw(&sha256.header,
                             CX_LAST,
                             data,
                             payload_length,
                             G_swap_ctx.sha256_digest,
                             sizeof(G_swap_ctx.sha256_digest)) != CX_OK) {
            PRINTF("Error: cx_hash_no_throw\n");
            return reply_error(INTERNAL_ERROR);
        }

        PRINTF("sha256_digest: %.*H\n", 32, G_swap_ctx.sha256_digest);

        PRINTF("payload_length = %d\n", payload_length);
        for (int i = 0; i < payload_length; ++i) {
            PRINTF("%02x", data[i]);
        }
        PRINTF("\n");

        int n = base64_decode(payload,
                              sizeof(payload),
                              (const unsigned char *) data,
                              payload_length);
        if (n < 0) {
            PRINTF("Error: Can't decode SELL/FUND/NG transaction base64\n");

            return reply_error(DESERIALIZATION_FAILED);
        }
        PRINTF("payload_length = %d\n", payload_length);
        for (int i = 0; i < payload_length; ++i) {
            PRINTF("%02x", data[i]);
        }
        PRINTF("\n");
        PRINTF("payload length = %d\n", n);
        for (int i = 0; i < n; ++i) {
            PRINTF("%02x", payload[i]);
        }
        PRINTF("\n");

        PRINTF("len(base64_decode(payload)) = %d\n", n);
        for (int i = 0; i < n; ++i)
        {
            PRINTF("%02x", payload[i]);
        }
        PRINTF("\n");

        stream = pb_istream_from_buffer(payload, n);

        if (cmd->subcommand == SELL || cmd->subcommand == SELL_NG) {
            if (!pb_decode(&stream, ledger_swap_NewSellResponse_fields, &G_swap_ctx.sell_transaction)) {
                PRINTF("Error: Can't parse SELL transaction protobuf\n");
                return reply_error(DESERIALIZATION_FAILED);
            }
            // Field not received from protobuf
            G_swap_ctx.sell_transaction_extra_id[0] = '\0';
        } else if (cmd->subcommand == FUND || cmd->subcommand == FUND_NG) {
            if (!pb_decode(&stream, ledger_swap_NewFundResponse_fields, &G_swap_ctx.fund_transaction)) {
                PRINTF("Error: Can't parse FUND transaction protobuf\n");
                return reply_error(DESERIALIZATION_FAILED);
            }
            // Field not received from protobuf
            G_swap_ctx.fund_transaction_extra_id[0] = '\0';
        } else {
            if (!pb_decode(&stream, ledger_swap_NewTransactionResponse_fields, &G_swap_ctx.received_transaction)) {
                PRINTF("Error: Can't parse SWAP transaction protobuf\n");
                return reply_error(DESERIALIZATION_FAILED);
            }
        }

        // trim leading 0s
        if (cmd->subcommand == SELL || cmd->subcommand == SELL_NG) {
            trim_pb_bytes_array((pb_bytes_array_16_t *) &G_swap_ctx.sell_transaction.in_amount);
        } else if (cmd->subcommand == FUND || cmd->subcommand == FUND_NG) {
            trim_pb_bytes_array((pb_bytes_array_16_t *) &G_swap_ctx.fund_transaction.in_amount);
        } else {
            normalize_currencies();
        }

        pb_bytes_array_32_t *tx_id;
        if (G_swap_ctx.subcommand == SELL || cmd->subcommand == SELL_NG) {
            tx_id = (pb_bytes_array_32_t *) &G_swap_ctx.sell_transaction.device_transaction_id;
            PRINTF("G_swap_ctx.sell_transaction->device_transaction_id @%p: %.*H\n",
                   G_swap_ctx.sell_transaction.device_transaction_id.bytes,
                   G_swap_ctx.sell_transaction.device_transaction_id.size,
                   G_swap_ctx.sell_transaction.device_transaction_id.bytes);
        } else if (cmd->subcommand == FUND || cmd->subcommand == FUND_NG) {
            tx_id = (pb_bytes_array_32_t *) &G_swap_ctx.fund_transaction.device_transaction_id;
            PRINTF("G_swap_ctx.fund_transaction->device_transaction_id @%p: %.*H\n",
                   G_swap_ctx.fund_transaction.device_transaction_id.bytes,
                   G_swap_ctx.fund_transaction.device_transaction_id.size,
                   G_swap_ctx.fund_transaction.device_transaction_id.bytes);
        } else {
            tx_id = (pb_bytes_array_32_t *) &G_swap_ctx.received_transaction.device_transaction_id_ng;
            PRINTF("G_swap_ctx.received_transaction->device_transaction_id_ng @%p: %.*H\n",
                   G_swap_ctx.received_transaction.device_transaction_id_ng.bytes,
                   G_swap_ctx.received_transaction.device_transaction_id_ng.size,
                   G_swap_ctx.received_transaction.device_transaction_id_ng.bytes);
        }

        if (tx_id->size != sizeof(G_swap_ctx.device_transaction_id.sell_fund)) {
            PRINTF("Error: Device transaction ID (SELL/FUND) size doesn't match\n");
            PRINTF("tx_id->size = %d\n", tx_id->size);
            PRINTF("sizeof(G_swap_ctx.device_transaction_id.sell_fund) = %d\n",
                   sizeof(G_swap_ctx.device_transaction_id.sell_fund));
        }
        if (memcmp(G_swap_ctx.device_transaction_id.sell_fund, tx_id->bytes, tx_id->size) != 0) {
            PRINTF("Error: Device transaction IDs (SELL/FUND) don't match\n");
            PRINTF("G_swap_ctx.device_transaction_id @%p: %.*H\n",
                   G_swap_ctx.device_transaction_id.sell_fund,
                   sizeof(G_swap_ctx.device_transaction_id.sell_fund),
                   G_swap_ctx.device_transaction_id.sell_fund);

            return reply_error(WRONG_TRANSACTION_ID);
        }
    }

    if (cmd->data.size < 1 + payload_length + 1) {
        PRINTF("Error: Can't parse process_transaction message, should include fee\n");

        return reply_error(DESERIALIZATION_FAILED);
    }

    G_swap_ctx.transaction_fee_length = data[payload_length];
    PRINTF("G_swap_ctx.transaction_fee_length = %d\n", G_swap_ctx.transaction_fee_length);
    PRINTF("G_swap_ctx.transaction_fee_length = %d\n", G_swap_ctx.transaction_fee_length);

    if (G_swap_ctx.transaction_fee_length > sizeof(G_swap_ctx.transaction_fee)) {
        PRINTF("Error: Transaction fee is to long\n");

        return reply_error(DESERIALIZATION_FAILED);
    }

    if (cmd->data.size < 1 + payload_length + 1 + G_swap_ctx.transaction_fee_length) {
        PRINTF("Error: Input buffer is too small");

        return reply_error(DESERIALIZATION_FAILED);
    }

    memset(G_swap_ctx.transaction_fee, 0, sizeof(G_swap_ctx.transaction_fee));
    memcpy(G_swap_ctx.transaction_fee,
           data + payload_length + 1,
           G_swap_ctx.transaction_fee_length);
    PRINTF("Transaction fees BE = %.*H\n",
           G_swap_ctx.transaction_fee_length,
           G_swap_ctx.transaction_fee);

    if (reply_success() < 0) {
        PRINTF("Error: failed to send response\n");

        return -1;
    }

    G_swap_ctx.state = TRANSACTION_RECEIVED;

    return 0;
}
