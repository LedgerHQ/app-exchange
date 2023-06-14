from ragger.utils import create_currency_config
from ragger.bip import BtcDerivationPathFormat, bitcoin_pack_derivation_path

LTC_CONF = create_currency_config("LTC", "Litecoin")

LTC_PACKED_DERIVATION_PATH = bitcoin_pack_derivation_path(BtcDerivationPathFormat.P2SH, "m/49'/02'/0'/0/0")


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
