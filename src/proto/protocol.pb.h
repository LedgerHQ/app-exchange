/* Automatically generated nanopb header */
/* Generated by nanopb-0.3.9 at Tue May  6 15:05:16 2025. */

#ifndef PB_LEDGER_SWAP_PROTOCOL_PB_H_INCLUDED
#define PB_LEDGER_SWAP_PROTOCOL_PB_H_INCLUDED
#include <pb.h>

/* @@protoc_insertion_point(includes) */
#if PB_PROTO_HEADER_VERSION != 30
#error Regenerate this file with the current version of nanopb generator.
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Struct definitions */
typedef PB_BYTES_ARRAY_T(16) ledger_swap_NewFundResponse_in_amount_t;
typedef PB_BYTES_ARRAY_T(32) ledger_swap_NewFundResponse_device_transaction_id_t;
typedef struct _ledger_swap_NewFundResponse {
    char user_id[50];
    char account_name[50];
    char in_currency[10];
    ledger_swap_NewFundResponse_in_amount_t in_amount;
    char in_address[151];
    ledger_swap_NewFundResponse_device_transaction_id_t device_transaction_id;
    char in_extra_id[20];
/* @@protoc_insertion_point(struct:ledger_swap_NewFundResponse) */
} ledger_swap_NewFundResponse;

typedef PB_BYTES_ARRAY_T(33) ledger_swap_NewTransactionResponse_payin_extra_data_t;
typedef PB_BYTES_ARRAY_T(16) ledger_swap_NewTransactionResponse_amount_to_provider_t;
typedef PB_BYTES_ARRAY_T(16) ledger_swap_NewTransactionResponse_amount_to_wallet_t;
typedef PB_BYTES_ARRAY_T(32) ledger_swap_NewTransactionResponse_device_transaction_id_ng_t;
typedef struct _ledger_swap_NewTransactionResponse {
    char payin_address[151];
    char payin_extra_id[20];
    char refund_address[151];
    char refund_extra_id[20];
    char payout_address[151];
    char payout_extra_id[20];
    char currency_from[10];
    char currency_to[10];
    ledger_swap_NewTransactionResponse_amount_to_provider_t amount_to_provider;
    ledger_swap_NewTransactionResponse_amount_to_wallet_t amount_to_wallet;
    char device_transaction_id[11];
    ledger_swap_NewTransactionResponse_device_transaction_id_ng_t device_transaction_id_ng;
    ledger_swap_NewTransactionResponse_payin_extra_data_t payin_extra_data;
/* @@protoc_insertion_point(struct:ledger_swap_NewTransactionResponse) */
} ledger_swap_NewTransactionResponse;

typedef PB_BYTES_ARRAY_T(16) ledger_swap_UDecimal_coefficient_t;
typedef struct _ledger_swap_UDecimal {
    ledger_swap_UDecimal_coefficient_t coefficient;
    uint32_t exponent;
/* @@protoc_insertion_point(struct:ledger_swap_UDecimal) */
} ledger_swap_UDecimal;

typedef PB_BYTES_ARRAY_T(16) ledger_swap_NewSellResponse_in_amount_t;
typedef PB_BYTES_ARRAY_T(32) ledger_swap_NewSellResponse_device_transaction_id_t;
typedef struct _ledger_swap_NewSellResponse {
    char trader_email[50];
    char in_currency[10];
    ledger_swap_NewSellResponse_in_amount_t in_amount;
    char in_address[151];
    char out_currency[10];
    ledger_swap_UDecimal out_amount;
    ledger_swap_NewSellResponse_device_transaction_id_t device_transaction_id;
    char in_extra_id[20];
/* @@protoc_insertion_point(struct:ledger_swap_NewSellResponse) */
} ledger_swap_NewSellResponse;

/* Default values for struct fields */

/* Initializer values for message structs */
#define ledger_swap_NewTransactionResponse_init_default {"", "", "", "", "", "", "", "", {0, {0}}, {0, {0}}, "", {0, {0}}, {0, {0}}}
#define ledger_swap_UDecimal_init_default        {{0, {0}}, 0}
#define ledger_swap_NewSellResponse_init_default {"", "", {0, {0}}, "", "", ledger_swap_UDecimal_init_default, {0, {0}}, ""}
#define ledger_swap_NewFundResponse_init_default {"", "", "", {0, {0}}, "", {0, {0}}, ""}
#define ledger_swap_NewTransactionResponse_init_zero {"", "", "", "", "", "", "", "", {0, {0}}, {0, {0}}, "", {0, {0}}, {0, {0}}}
#define ledger_swap_UDecimal_init_zero           {{0, {0}}, 0}
#define ledger_swap_NewSellResponse_init_zero    {"", "", {0, {0}}, "", "", ledger_swap_UDecimal_init_zero, {0, {0}}, ""}
#define ledger_swap_NewFundResponse_init_zero    {"", "", "", {0, {0}}, "", {0, {0}}, ""}

/* Field tags (for use in manual encoding/decoding) */
#define ledger_swap_NewFundResponse_user_id_tag  1
#define ledger_swap_NewFundResponse_account_name_tag 2
#define ledger_swap_NewFundResponse_in_currency_tag 3
#define ledger_swap_NewFundResponse_in_amount_tag 4
#define ledger_swap_NewFundResponse_in_address_tag 5
#define ledger_swap_NewFundResponse_in_extra_id_tag 7
#define ledger_swap_NewFundResponse_device_transaction_id_tag 6
#define ledger_swap_NewTransactionResponse_payin_address_tag 1
#define ledger_swap_NewTransactionResponse_payin_extra_id_tag 2
#define ledger_swap_NewTransactionResponse_payin_extra_data_tag 13
#define ledger_swap_NewTransactionResponse_refund_address_tag 3
#define ledger_swap_NewTransactionResponse_refund_extra_id_tag 4
#define ledger_swap_NewTransactionResponse_payout_address_tag 5
#define ledger_swap_NewTransactionResponse_payout_extra_id_tag 6
#define ledger_swap_NewTransactionResponse_currency_from_tag 7
#define ledger_swap_NewTransactionResponse_currency_to_tag 8
#define ledger_swap_NewTransactionResponse_amount_to_provider_tag 9
#define ledger_swap_NewTransactionResponse_amount_to_wallet_tag 10
#define ledger_swap_NewTransactionResponse_device_transaction_id_tag 11
#define ledger_swap_NewTransactionResponse_device_transaction_id_ng_tag 12
#define ledger_swap_UDecimal_coefficient_tag     1
#define ledger_swap_UDecimal_exponent_tag        2
#define ledger_swap_NewSellResponse_trader_email_tag 1
#define ledger_swap_NewSellResponse_in_currency_tag 2
#define ledger_swap_NewSellResponse_in_amount_tag 3
#define ledger_swap_NewSellResponse_in_address_tag 4
#define ledger_swap_NewSellResponse_in_extra_id_tag 8
#define ledger_swap_NewSellResponse_out_currency_tag 5
#define ledger_swap_NewSellResponse_out_amount_tag 6
#define ledger_swap_NewSellResponse_device_transaction_id_tag 7

/* Struct field encoding specification for nanopb */
extern const pb_field_t ledger_swap_NewTransactionResponse_fields[14];
extern const pb_field_t ledger_swap_UDecimal_fields[3];
extern const pb_field_t ledger_swap_NewSellResponse_fields[9];
extern const pb_field_t ledger_swap_NewFundResponse_fields[8];

/* Maximum encoded size of messages (where known) */
#define ledger_swap_NewTransactionResponse_size  670
#define ledger_swap_UDecimal_size                24
#define ledger_swap_NewSellResponse_size         330
#define ledger_swap_NewFundResponse_size         344

/* Message IDs (where set with "msgid" option) */
#ifdef PB_MSGID

#define PROTOCOL_MESSAGES \


#endif

#ifdef __cplusplus
} /* extern "C" */
#endif
/* @@protoc_insertion_point(eof) */

#endif
