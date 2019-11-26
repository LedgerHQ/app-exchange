#ifndef BTCHIP_ALTCOIN_CONTEXT_H

#define BTCHIP_ALTCOIN_CONTEXT_H

/**
 * Structure to configure the bitcoin application for a given altcoin
 * 
 */
typedef enum btchip_coin_flags_e {
    FLAG_PEERCOIN_UNITS=1,
    FLAG_PEERCOIN_SUPPORT=2,
    FLAG_SEGWIT_CHANGE_SUPPORT=4
} btchip_coin_flags_t;


typedef enum btchip_coin_kind_e {
    COIN_KIND_BITCOIN_TESTNET,
    COIN_KIND_BITCOIN,
    COIN_KIND_BITCOIN_CASH,
    COIN_KIND_BITCOIN_GOLD,
    COIN_KIND_LITECOIN,
    COIN_KIND_DOGE,
    COIN_KIND_DASH,
    COIN_KIND_ZCASH,
    COIN_KIND_KOMODO,
    COIN_KIND_RFU,
    COIN_KIND_STRATIS,
    COIN_KIND_PEERCOIN,
    COIN_KIND_PIVX,
    COIN_KIND_STEALTH,
    COIN_KIND_VIACOIN,
    COIN_KIND_VERTCOIN,
    COIN_KIND_DIGIBYTE,
    COIN_KIND_QTUM,
    COIN_KIND_BITCOIN_PRIVATE,
    COIN_KIND_HORIZEN,
    COIN_KIND_GAMECREDITS,
    COIN_KIND_ZCOIN, 
    COIN_KIND_ZCLASSIC,
    COIN_KIND_XSN,
    COIN_KIND_NIX,
    COIN_KIND_LBRY,
    COIN_KIND_RESISTANCE
} btchip_coin_kind_t;

typedef struct btchip_altcoin_config_s {
    unsigned short p2pkh_version;
    unsigned short p2sh_version;
    unsigned char family;
    //unsigned char* iconsuffix;// will use the icon provided on the stack (maybe)
#ifdef TARGET_BLUE
    const char* header_text;
    unsigned int color_header;
    unsigned int color_dashboard;
#endif // TARGET_BLUE
    const char* coinid; // used coind id for message signature prefix
    const char* name; // for ux displays
    const char* name_short; // for unit in ux displays
    const char* native_segwit_prefix; // null if no segwit prefix
    unsigned int forkid;
    btchip_coin_kind_t kind;
    unsigned int flags;
} btchip_altcoin_config_t;

#endif