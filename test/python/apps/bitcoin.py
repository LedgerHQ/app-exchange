# 0x3 BTC 0x7 Bitcoin 0x0
BTC_CONF = bytes([
    0x03, 0x42, 0x54, 0x43, 0x07, 0x42, 0x69, 0x74, 0x63, 0x6F, 0x69, 0x6E,
    0x00]);
BTC_CONF_DER_SIGNATURE = bytes([
    0x30, 0x45, 0x02, 0x21, 0x00, 0xCB, 0x17, 0x43, 0x82, 0x30, 0x22, 0x19,
    0xDC, 0xA3, 0x59, 0xC0, 0xA4, 0xD4, 0x57, 0xB2, 0x56, 0x9E, 0x31, 0xA0,
    0x6B, 0x2C, 0x25, 0xC0, 0x08, 0x8A, 0x2B, 0xD3, 0xFD, 0x6C, 0x04, 0x38,
    0x6A, 0x02, 0x20, 0x2C, 0x6D, 0x0A, 0x5B, 0x92, 0x4A, 0x41, 0x46, 0x21,
    0x06, 0x7E, 0x31, 0x6F, 0x02, 0x1A, 0xA1, 0x3A, 0xA5, 0xB2, 0xEE, 0xE2,
    0xBF, 0x36, 0xEA, 0x3C, 0xFD, 0xDE, 0xBC, 0x05, 0x3B, 0x20, 0x1B]);

# Address format (BTC-specific) + length (5) + 44'/0'/0'/0/0
# Possible address formats are:
# - legacy:  0
# - p2sh:    1
# - bech32:  2
## - 3 is skipped as it was used for "cashaddr" format
# - bech32m: 4
BTC_PACKED_DERIVATION_PATH = bytes([0x02,
                                    0x05,
                                    0x80, 0x00, 0x00, 0x2c,   # purpose
                                    0x80, 0x00, 0x00, 0x00,   # coin
                                    0x80, 0x00, 0x00, 0x00,   # account
                                    0x00, 0x00, 0x00, 0x00,   # change
                                    0x00, 0x00, 0x00, 0x00])  # address index


class Command:
    SET_USER_KEYCARD = 0x10
    SETUP_SECURE_SCREEN = 0x12
    SET_ALTERNATE_COIN_VER = 0x14
    GET_COIN_VER = 0x16
    SETUP = 0x20
    VERIFY_PIN = 0x22
    GET_OPERATION_MODE = 0x24
    SET_OPERATION_MODE = 0x26
    SET_KEYBOARD_CFG = 0x28
    GET_WALLET_PUBLIC_KEY = 0x40
    GET_TRUSTED_INPUT = 0x42
    HASH_INPUT_START = 0x44
    HASH_INPUT_FINALIZE = 0x46
    HASH_SIGN = 0x48
    HASH_INPUT_FINALIZE_FULL = 0x4A
    GET_INTERNAL_CHAIN_INDEX = 0x4C
    SIGN_MESSAGE = 0x4E
    GET_TRANSACTION_LIMIT = 0xA0
    SET_TRANSACTION_LIMIT = 0xA2
    IMPORT_PRIVATE_KEY = 0xB0
    GET_PUBLIC_KEY = 0xB2
    DERIVE_BIP32_KEY = 0xB4
    SIGNVERIFY_IMMEDIATE = 0xB6
    GET_RANDOM = 0xC0
    GET_ATTESTATION = 0xC2
    GET_FIRMWARE_VERSION = 0xC4
    COMPOSE_MOFN_ADDRESS = 0xC6
    GET_POS_SEED = 0xCA
    DEBUG = 0xD0


class BitcoinClient:
    CLA = 0xE0
    def __init__(self, client):
        self._client = client
        self._hash_ongoing = False
        self._get_ongoing = False

    @property
    def client(self):
        return self._client

    def _exchange(self,
                  ins: int,
                  p1: int = 0x00,
                  p2: int = 0x00,
                  payload: bytes = b''):
        return self.client.exchange(self.CLA, ins=ins, p1=p1, p2=p2, data=payload)

    def get_public_key(self, payload):
        return self._exchange(Command.GET_WALLET_PUBLIC_KEY, p2=0x02, payload=payload)

    def get_coin_version(self):
        return self._exchange(Command.GET_COIN_VER)

    def get_trusted_input(self, payload):
        p1 = 0x80 if self._get_ongoing else 0x00
        result = self._exchange(Command.GET_TRUSTED_INPUT, p1=p1, payload=payload)
        self._get_ongoing = True
        return result

    def hash_input(self, payload, finalize=False):
        ins = Command.HASH_INPUT_FINALIZE_FULL if finalize else Command.HASH_INPUT_START
        p1 = 0x80 if self._hash_ongoing else 0x00
        p2 = 0x00 if finalize else 0x02
        result = self._exchange(ins, p1=p1, p2=p2, payload=payload)
        self._hash_ongoing = True
        return result
