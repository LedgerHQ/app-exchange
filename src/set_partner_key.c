#include "set_partner_key.h"
#include "apdu_offsets.h"
#include "os.h"
#include "errors.h"

#ifdef TEST_PUBLIC_KEY
// this key was created from private key sha256('Ledger'), see test/tools folder
unsigned char LedgerPubKey[] = {
    0x02, 0x05, 0xc5, 0x2e, 0xc5, 0xfe, 0x24, 0x5a, 0x55, 0x7b,
    0x86, 0x1d, 0x22, 0x18, 0x50, 0x1a, 0x81, 0x2d, 0x32, 0xe0,
    0x34, 0xe1, 0x5e, 0x9d, 0x96, 0x1c, 0x1b, 0x1a, 0x13, 0x8c, 0x7f, 0xb1, 0x49};
#else
unsigned char LedgerPubKey[] = {};
#endif

const unsigned char CURVE_SIZE_BYTES = 32;
const unsigned char PUB_KEY_LENGTH = CURVE_SIZE_BYTES + 1;

// DER serialize R and S part of signature [30 L 02 Lr r 02 Ls s]
unsigned char der_serialize(unsigned char* R, unsigned char r_length, unsigned char* S, unsigned char s_length, unsigned char* der, unsigned char output_buffer_size) {
    //                         30  L  02   Lr  r          02  Ls  s
    unsigned int der_length = 1 + 1 + 1 + 1 + r_length + 1 + 1 + s_length;
    if (der_length > output_buffer_size) {
        PRINTF("Error: Output buffer for DER is too small");
        THROW(OUTPUT_BUFFER_IS_TOO_SMALL);
    }
    unsigned char off = 0;
    der[off++] = 30;
    der[off++] = der_length - 2; // do not count first to bytes [30, L]
    der[off++] = 2;
    der[off++] = r_length;
    os_memcpy(der + off, R, r_length);
    off += r_length;
    der[off++] = 2;
    der[off++] = s_length;
    os_memcpy(der + off, S, s_length);
    off += s_length;
    return off;
}

int set_partner_key(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length) {
    // data is serialized as
    // 1 byte - partner name length L
    // L bytes - partner name
    // 33 bytes - partner public key
    // 32 bytes - R part of signature
    // 32 bytes - S part of signature
    if (input_buffer_length < OFFSET_CDATA) {
        PRINTF("Error: Input buffer is too small");
        THROW(INCORRECT_COMMAND_DATA);
    }
    ctx->partner.name_length = input_buffer[OFFSET_CDATA];
    const unsigned char name_offset = OFFSET_CDATA + 1;
    const unsigned char pub_key_offset = name_offset + ctx->partner.name_length;
    const unsigned char r_offset = pub_key_offset + PUB_KEY_LENGTH;
    const unsigned char s_offset = r_offset + CURVE_SIZE_BYTES;
    const unsigned char signed_data_length = 1 + ctx->partner.name_length + PUB_KEY_LENGTH;
    if (output_buffer_length < 2) {
        PRINTF("Error: Output buffer is too small");
        THROW(OUTPUT_BUFFER_IS_TOO_SMALL);
    }
    if (s_offset + CURVE_SIZE_BYTES > input_buffer_length) {
        PRINTF("Error: Input buffer is too small to contain correct SET_PARTNER_KEY message");
        THROW(INCORRECT_COMMAND_DATA);
    }
    if ((ctx->partner.name_length < 3) || (ctx->partner.name_length > 15)) {
        PRINTF("Error: Partner name length should be in [3, 15]");
        THROW(INCORRECT_COMMAND_DATA);
    }
    // check signature
    unsigned char hash[CURVE_SIZE_BYTES];
    cx_hash_sha256(input_buffer + OFFSET_CDATA, signed_data_length, hash, CURVE_SIZE_BYTES);
    cx_ecfp_256_public_key_t key;
    cx_ecfp_init_public_key(CX_CURVE_SECP256K1, LedgerPubKey, sizeof(LedgerPubKey), &key);
    unsigned char der[6 + 2 * CURVE_SIZE_BYTES];
    unsigned char der_length = der_serialize(input_buffer + r_offset, CURVE_SIZE_BYTES, input_buffer + s_offset, CURVE_SIZE_BYTES, der, sizeof(der));
    if (cx_ecdsa_verify(&key, CX_LAST, CX_SHA256, hash, CURVE_SIZE_BYTES, der, der_length) == 0) {
        PRINTF("Error: Fail to verify signature of partner name and public key");
        THROW(SIGN_VERIFICATION_FAIL);
    }
    os_memcpy(ctx->partner.name, input_buffer + name_offset, ctx->partner.name_length);
    cx_ecfp_init_public_key(CX_CURVE_SECP256K1, input_buffer + pub_key_offset, PUB_KEY_LENGTH, &ctx->partner.public_key);
    ctx->state = PROVIDER_SETTED;
    output_buffer[0] = 0x90;
    output_buffer[1] = 0x00;
    return 2;
}