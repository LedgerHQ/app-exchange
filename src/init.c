#include "init.h"
#include "cx.h"

// Init public keys
void init_application_context(swap_app_context_t* ctx) {
#ifdef TEST_PUBLIC_KEY
    // this key was created from private key sha256('Ledger'), see test/tools folder
    unsigned char LedgerPubKey[] = {
        0x4,
        0x5, 0xC5, 0x2E, 0xC5, 0xFE, 0x24, 0x5A, 0x55,
        0x7B, 0x86, 0x1D, 0x22, 0x18, 0x50, 0x1A, 0x81,
        0x2D, 0x32, 0xE0, 0x34, 0xE1, 0x5E, 0x9D, 0x96,
        0x1C, 0x1B, 0x1A, 0x13, 0x8C, 0x7F, 0xB1, 0x49,
        
        0x6B, 0x4F, 0xBA, 0x66, 0x65, 0x56, 0x66, 0x62,
        0x3E, 0xB7, 0x8C, 0x93, 0xE9, 0xF0, 0x0, 0x8F,
        0xCC, 0xA6, 0xA, 0x53, 0x85, 0x88, 0x13, 0x1A,
        0x2A, 0xC7, 0xBA, 0x98, 0xE1, 0xF6, 0x20, 0xCE};
#else
    unsigned char LedgerPubKey[] = {};
#endif

    cx_ecfp_init_public_key(CX_CURVE_SECP256K1, LedgerPubKey, sizeof(LedgerPubKey), &(ctx->ledger_public_key));
    unsigned char rawKey[32];
    cx_hash_sha256("Ledger", 6, rawKey, 32);
    cx_ecfp_256_private_key_t privKey; 
    cx_ecfp_256_public_key_t pubKey; 
    cx_ecfp_init_private_key(CX_CURVE_SECP256K1, rawKey, 32, &privKey);
    if (os_memcmp(privKey.d, rawKey, sizeof(rawKey)) != 0) {
        PRINTF("NOT EQ!!!");
        return;
    }
    cx_ecfp_generate_pair(CX_CURVE_SECP256K1, &pubKey, &privKey, 1);
    if (os_memcmp(pubKey.W, LedgerPubKey, sizeof(LedgerPubKey)) != 0) {
        PRINTF("NOT EQ!!!");
        return;
    }
    unsigned char input_buffer[] ={9, 83, 87, 65, 80, 95, 84, 69, 83, 84, 3, 102, 10, 21, 3, 9, 251, 82, 243, 212, 44, 39, 173, 4, 220, 49, 153, 170, 35, 55, 189, 42, 138, 0, 44, 83, 55, 209, 120, 138, 227, 71, 211};
    unsigned char original_der_signature[] = {30, 68, 2, 32, 21, 27, 220, 119, 44, 237, 37, 134, 60, 89, 70, 189, 167, 129, 36, 188, 21, 164, 13, 96, 47, 190, 69, 143, 126, 219, 132, 4, 111, 149, 194, 129, 2, 32, 105, 170, 192, 53, 43, 149, 95, 118, 121, 102, 179, 22, 212, 63, 207, 216, 56, 32, 57, 52, 185, 220, 232, 238, 62, 140, 225, 100, 190, 87, 193, 223};
    unsigned char der_signature[70];
    unsigned char hash[32];
    cx_hash_sha256(input_buffer, sizeof(input_buffer), hash, 32);
    unsigned int info = 0;
    cx_ecdsa_sign(&privKey, CX_LAST | CX_RND_TRNG, CX_SHA256, hash, 32, der_signature, 70, &info);
    /*if (os_memcmp(original_der_signature, der_signature, 70) != 0) {
        PRINTF("NOT EQ!!!");
        return;
    }*/
    if (cx_ecdsa_verify(&(ctx->ledger_public_key), CX_LAST | CX_RND_TRNG, CX_SHA256, hash, 32, der_signature, 70) == 0) {
        PRINTF("Error: Fail to verify signature of partner name and public key");
        return;
    }
    ctx->state = INITIAL_STATE;
}