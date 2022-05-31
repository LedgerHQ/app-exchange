# 0x3 LTC 0x8 Litecoin 0x0
LTC_CONF = bytes([
    0x03, 0x4C, 0x54, 0x43, 0x08, 0x4C, 0x69, 0x74, 0x65, 0x63, 0x6F, 0x69,
    0x6E, 0x00
])

LTC_CONF_DER_SIGNATURE = bytes([
    0x30, 0x45, 0x02, 0x21, 0x00, 0x98, 0xF7, 0x0A, 0xD7, 0xD7, 0x57, 0xE3,
    0x45, 0x2E, 0xE2, 0x97, 0x21, 0x5B, 0xE6, 0x0C, 0xE0, 0x18, 0x87, 0xCF,
    0xAB, 0x29, 0xF9, 0x98, 0x11, 0x34, 0x32, 0x82, 0x3F, 0x94, 0xD3, 0x5B,
    0x88, 0x02, 0x20, 0x31, 0xE1, 0x41, 0x9C, 0xF1, 0xCE, 0x94, 0x34, 0x01,
    0xE5, 0x70, 0x32, 0x52, 0x8E, 0x3A, 0x99, 0xEC, 0x7D, 0x33, 0x86, 0x65,
    0x26, 0x5D, 0xED, 0xF2, 0x5B, 0xEC, 0xA4, 0x5F, 0x49, 0x52, 0xFB
])


# Address format (BTC-specific) length (5) + 44'/02'/0'/0/0
# Possible address format are:
# - legacy:  0
# - p2sh:    1
# - bech32:  2
## - 3 is skipped as it was used for "cashaddr" format
# - bech32m: 4

LTC_PACKED_DERIVATION_PATH = bytes([0x01,
                                    0x05,
                                    0x80, 0x00, 0x00, 0x31,
                                    0x80, 0x00, 0x00, 0x02,
                                    0x80, 0x00, 0x00, 0x00,
                                    0x00, 0x00, 0x00, 0x00,
                                    0x00, 0x00, 0x00, 0x00])

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


class LitecoinClient:
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
