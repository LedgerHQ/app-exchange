#include "init.h"
#include "cx.h"

// Init public keys
void init_application_context(swap_app_context_t* ctx) {
#ifdef TEST_PUBLIC_KEY
    // this key was created from private key sha256('Ledger'), see test/tools folder
    unsigned char LedgerPubKey[] = {
        0x02, 0x05, 0xc5, 0x2e, 0xc5, 0xfe, 0x24, 0x5a, 0x55, 0x7b,
        0x86, 0x1d, 0x22, 0x18, 0x50, 0x1a, 0x81, 0x2d, 0x32, 0xe0,
        0x34, 0xe1, 0x5e, 0x9d, 0x96, 0x1c, 0x1b, 0x1a, 0x13, 0x8c, 0x7f, 0xb1, 0x49};
#else
    unsigned char LedgerPubKey[] = {};
#endif
    cx_ecfp_init_public_key(CX_CURVE_SECP256K1, LedgerPubKey, sizeof(LedgerPubKey), &ctx->ledger_public_key);
    ctx->state = INITIAL_STATE;
}