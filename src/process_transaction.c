#include "process_transaction.h"
#include "pb_decode.h"
#include "protocol.pb.h"
#include "swap_errors.h"
#include "reply_error.h"
#include "base64.h"

typedef struct currency_alias_s{
    char* foreign_name;
    char* ledger_name;
} currency_alias_t;

const currency_alias_t const currencies_aliases[] = {
    {"USDT20", "USDT"}, // Changelly's name must be changed to match the ticker from Ledger's cryptoasset list
    {"REP", "REPV2"} // Changelly's name isn't up to date...
};

void to_uppercase(char *str, unsigned char size) {
    for (unsigned char i = 0; i < size && str[i] != 0; i++) {
        str[i] = str[i] >= 'a' ? str[i] - ('a' - 'A') : str[i];
    }
}

void set_ledger_currency_name(char* currency){
    for(size_t i=0; i<sizeof(currencies_aliases)/sizeof(currencies_aliases[0]); i++){
        if(!strcmp(currency, (char*)(PIC(currencies_aliases[i].foreign_name)))){
            strcpy(currency, (char*)(PIC(currencies_aliases[i].ledger_name)));
            return;
        }
    }
}

void normalize_currencies(swap_app_context_t *ctx) {

    to_uppercase(ctx->received_transaction.currency_from,
                sizeof(ctx->received_transaction.currency_from));
    to_uppercase(ctx->received_transaction.currency_to,
                sizeof(ctx->received_transaction.currency_to));

    set_ledger_currency_name(ctx->received_transaction.currency_from);
    set_ledger_currency_name(ctx->received_transaction.currency_to);

    // strip bcash CashAddr header, and other bip21 like headers
    for(size_t i=0; i < sizeof(ctx->received_transaction.payin_address); i++){
        if(ctx->received_transaction.payin_address[i] == ':'){
            memmove(ctx->received_transaction.payin_address,
                    ctx->received_transaction.payin_address + i + 1,
                    sizeof(ctx->received_transaction.payin_address) - i - 1);
            break;
        }
    }
}

int process_transaction(subcommand_e subcommand,
                        swap_app_context_t *ctx,
                        const buf_t *input,
                        SendFunction send) {
    if (input->size < 1) {
        PRINTF("Error: Can't parse process_transaction message, length should be more then 1");

        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }

    size_t payload_length = input->bytes[0];
    if (input->size < 1 + payload_length) {
        PRINTF("Error: Can't parse process_transaction message, invalid payload length");

        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }

    pb_istream_t stream;
    cx_sha256_t sha256;

    cx_sha256_init(&sha256);

    PRINTF("len(payload): %d\n", payload_length);

    if (subcommand == SWAP) {
        stream = pb_istream_from_buffer(input->bytes + 1, payload_length);

        if (!pb_decode(&stream, ledger_swap_NewTransactionResponse_fields,
                       &ctx->received_transaction)) {
            PRINTF("Error: Can't parse SWAP transaction protobuf\n%.*H\n", payload_length, input->bytes + 1);

            return reply_error(ctx, DESERIALIZATION_FAILED, send);
        }

        if (os_memcmp(ctx->device_transaction_id.swap,
                      ctx->received_transaction.device_transaction_id,
                      sizeof(ctx->device_transaction_id.swap)) != 0) {
            PRINTF("Error: Device transaction IDs (SWAP) doesn't match");

            return reply_error(ctx, WRONG_TRANSACTION_ID, send);
        }

        normalize_currencies(ctx);
    }

    if (subcommand == SELL) {
        // arbitrary maximum payload size
        unsigned char payload[256];

        PRINTF("payload: %.*H\n", payload_length, input->bytes + 1);
        PRINTF("len(decode_base64(payload)): %d\n", n);

        int n = base64_decode(payload, sizeof(payload), (const unsigned char *) input->bytes + 1, payload_length);
        if (n < 0) {
            PRINTF("Error: Can't decode SELL transaction base64");

            return reply_error(ctx, DESERIALIZATION_FAILED, send);
        }

        PRINTF("decode_base64(payload): %.*H\n", n, payload);

        unsigned char dot = '.';

        cx_hash(&sha256.header, 0, (const unsigned char *) &dot, 1, NULL, 0);

        stream = pb_istream_from_buffer(payload, n);

        if (!pb_decode(&stream, ledger_swap_NewSellResponse_fields, &ctx->sell_transaction)) {
            PRINTF("Error: Can't parse SELL transaction protobuf");

            return reply_error(ctx, DESERIALIZATION_FAILED, send);
        }

        PRINTF("ctx->device_transaction_id: %.*H", 32, ctx->device_transaction_id.sell);

        if (os_memcmp(ctx->device_transaction_id.sell,
                      ctx->sell_transaction.device_transaction_id.bytes,
                      sizeof(ctx->device_transaction_id.sell)) != 0) {
            PRINTF("Error: Device transaction IDs (SELL) doesn't match");

            return reply_error(ctx, WRONG_TRANSACTION_ID, send);
        }
    }

    cx_hash(&sha256.header, CX_LAST, input->bytes + 1, payload_length, ctx->sha256_digest,
            sizeof(ctx->sha256_digest));

    PRINTF("sha256_digest: %.*H\n", 32, ctx->sha256_digest);

    if (input->size < 1 + payload_length + 1) {
        PRINTF("Error: Can't parse process_transaction message, should include fee");

        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }

    ctx->transaction_fee_length = input->bytes[1 + payload_length];

    if (ctx->transaction_fee_length > sizeof(ctx->transaction_fee)) {
        PRINTF("Error: Transaction fee is to long");

        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }

    if (input->size < 1 + payload_length + 1 + ctx->transaction_fee_length) {
        PRINTF("Error: Input buffer is too small");

        return reply_error(ctx, DESERIALIZATION_FAILED, send);
    }

    os_memset(ctx->transaction_fee, 0, sizeof(ctx->transaction_fee));
    os_memcpy(ctx->transaction_fee, input->bytes + 1 + payload_length + 1,
              ctx->transaction_fee_length);

    PRINTF("Transaction fees BE = %.*H\n", ctx->transaction_fee_length, ctx->transaction_fee);

    unsigned char output_buffer[2] = {0x90, 0x00};

    if (send(output_buffer, 2) < 0) {
        PRINTF("Error: failed to send response");

        return -1;
    }

    ctx->state = TRANSACTION_RECIEVED;

    return 0;
}
