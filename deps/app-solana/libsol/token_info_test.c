#include "common_byte_strings.h"
#include "util.h"
#include "token_info.h"
#include <assert.h>
#include <stdio.h>

void test_get_hardcoded_token_symbol_unknown() {
    Pubkey pubkey = {{BYTES32_BS58_1}};
    const char *symbol = get_hardcoded_token_symbol(pubkey.data);

    assert_string_equal(symbol, "???");
}

void test_get_hardcoded_token_symbol_USDC() {
    Pubkey pubkey = {{0xc6, 0xfa, 0x7a, 0xf3, 0xbe, 0xdb, 0xad, 0x3a, 0x3d, 0x65, 0xf3,
                      0x6a, 0xab, 0xc9, 0x74, 0x31, 0xb1, 0xbb, 0xe4, 0xc2, 0xd2, 0xf6,
                      0xe0, 0xe4, 0x7c, 0xa6, 0x02, 0x03, 0x45, 0x2f, 0x5d, 0x61}};
    const char *symbol = get_hardcoded_token_symbol(pubkey.data);

    assert_string_equal(symbol, "USDC");
}

void test_get_hardcoded_token_symbol_SOL() {
    Pubkey pubkey = {{0x06, 0x9b, 0x88, 0x57, 0xfe, 0xab, 0x81, 0x84, 0xfb, 0x68, 0x7f,
                      0x63, 0x46, 0x18, 0xc0, 0x35, 0xda, 0xc4, 0x39, 0xdc, 0x1a, 0xeb,
                      0x3b, 0x55, 0x98, 0xa0, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x01}};
    const char *symbol = get_hardcoded_token_symbol(pubkey.data);

    assert_string_equal(symbol, "SOL");
}

int main() {
    test_get_hardcoded_token_symbol_unknown();
    test_get_hardcoded_token_symbol_SOL();
    test_get_hardcoded_token_symbol_USDC();

    printf("passed\n");
    return 0;
}
