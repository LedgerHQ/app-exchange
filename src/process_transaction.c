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
    if (cmd->data.size < 1) {
        PRINTF("Error: Can't parse process_transaction message, length should be more than 1\n");

        return reply_error(DESERIALIZATION_FAILED);
    }

    uint16_t payload_length;
    uint8_t *data;
    if (cmd->subcommand == SWAP_NG) {
        payload_length = U2BE(cmd->data.bytes, 0);
        if (cmd->data.size < 2 + payload_length) {
            PRINTF("Error: Can't parse process_transaction message, invalid payload length\n");
            return reply_error(DESERIALIZATION_FAILED);
        }
        data = cmd->data.bytes + 2;
    } else {
        payload_length = cmd->data.bytes[0];
        if (cmd->data.size < 1 + payload_length) {
            PRINTF("Error: Can't parse process_transaction message, invalid payload length\n");
            return reply_error(DESERIALIZATION_FAILED);
        }
        data = cmd->data.bytes + 1;
    }

    pb_istream_t stream;
    cx_sha256_t sha256;

    cx_sha256_init(&sha256);

    PRINTF("len(payload): %d\n", payload_length);
    PRINTF("payload (%d): %.*H\n", payload_length, payload_length, data);

    if (cmd->subcommand == SWAP) {
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

        int n = base64_decode(payload,
                              sizeof(payload),
                              (const unsigned char *) data,
                              payload_length);
        PRINTF("base64_decoded\n");
        for (int i = 0; i < n; ++i)
        {
            PRINTF("%02x", payload[i]);
        }
        PRINTF("\n");

        PRINTF("len(base64_decode(payload)) = %d\n", n);

        if (n < 0) {
            PRINTF("Error: Can't decode SELL/FUND/NG transaction base64\n");

            return reply_error(DESERIALIZATION_FAILED);
        }

        PRINTF("decode_base64(payload): %.*H\n", n, payload);

        unsigned char dot = '.';

        if (cx_hash_no_throw(&sha256.header, 0, &dot, 1, NULL, 0) != CX_OK) {
            PRINTF("Error: cx_hash_no_throw\n");
            return reply_error(INTERNAL_ERROR);
        }

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
