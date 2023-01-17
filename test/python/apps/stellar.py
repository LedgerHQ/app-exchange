from enum import IntEnum, Enum, auto

from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config, RAPDU
from stellar_sdk import StrKey

XLM_CONF = create_currency_config("XLM", "Stellar")

XLM_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/148'/0'")

class Ins():
    GET_PUBLIC_KEY = 0x02
    SIGN = 0x04

class P1():
    NO_SIGNATURE = 0x00
    SIGNATURE = 0x01
    FIRST = 0x00
    MORE = 0x80

class P2():
    NON_CONFIRM = 0x00
    CONFIRM = 0x01
    LAST = 0x00
    MORE = 0x80

class Network(Enum):
    MAINNET = auto()
    TESTNET = auto()

network_id_public_hash = [
    0x7a, 0xc3, 0x39, 0x97, 0x54, 0x4e, 0x31, 0x75, 0xd2, 0x66, 0xbd, 0x02, 0x24, 0x39, 0xb2, 0x2c,
    0xdb, 0x16, 0x50, 0x8c, 0x01, 0x16, 0x3f, 0x26, 0xe5, 0xcb, 0x2a, 0x3e, 0x10, 0x45, 0xa9, 0x79
]

network_id_test_hash = [
    0xce, 0xe0, 0x30, 0x2d, 0x59, 0x84, 0x4d, 0x32, 0xbd, 0xca, 0x91, 0x5c, 0x82, 0x03, 0xdd, 0x44,
    0xb3, 0x3f, 0xbb, 0x7e, 0xdc, 0x19, 0x05, 0x1e, 0xa3, 0x7a, 0xbe, 0xdf, 0x28, 0xec, 0xd4, 0x72
]

networks_dict = {
    Network.MAINNET: bytes(network_id_public_hash),
    Network.TESTNET: bytes(network_id_test_hash),
}

class EnvelopeType(IntEnum):
    ENVELOPE_TYPE_TX = 2
    ENVELOPE_TYPE_TX_FEE_BUMP = 5

class CryptoKeyType(IntEnum):
    KEY_TYPE_ED25519 = 0
    KEY_TYPE_PRE_AUTH_T = 1
    KEY_TYPE_HASH_X = 2
    KEY_TYPE_ED25519_SIGNED_PAYLOAD = 3
    KEY_TYPE_MUXED_ED25519 = 0x100

class PreconditionType(IntEnum):
    PRECOND_NONE = 0
    PRECOND_TIME = 1
    PRECOND_V2 = 2

class MemoType(IntEnum):
    MEMO_NONE = 0
    MEMO_TEXT =1
    MEMO_ID = 2
    MEMO_HASH = 3
    MEMO_RETURN = 4

class XDROperationType(IntEnum):
    XDR_OPERATION_TYPE_CREATE_ACCOUNT = 0
    XDR_OPERATION_TYPE_PAYMENT = 1
    XDR_OPERATION_TYPE_PATH_PAYMENT_STRICT_RECEIVE = 2
    XDR_OPERATION_TYPE_MANAGE_SELL_OFFER = 3
    XDR_OPERATION_TYPE_CREATE_PASSIVE_SELL_OFFER = 4
    XDR_OPERATION_TYPE_SET_OPTIONS = 5
    XDR_OPERATION_TYPE_CHANGE_TRUST = 6
    XDR_OPERATION_TYPE_ALLOW_TRUST = 7
    XDR_OPERATION_TYPE_ACCOUNT_MERGE = 8
    XDR_OPERATION_TYPE_INFLATION = 9
    XDR_OPERATION_TYPE_MANAGE_DATA = 10
    XDR_OPERATION_TYPE_BUMP_SEQUENCE = 11
    XDR_OPERATION_TYPE_MANAGE_BUY_OFFER = 12
    XDR_OPERATION_TYPE_PATH_PAYMENT_STRICT_SEND = 13
    XDR_OPERATION_TYPE_CREATE_CLAIMABLE_BALANCE = 14
    XDR_OPERATION_TYPE_CLAIM_CLAIMABLE_BALANCE = 15
    XDR_OPERATION_TYPE_BEGIN_SPONSORING_FUTURE_RESERVES = 16
    XDR_OPERATION_TYPE_END_SPONSORING_FUTURE_RESERVES = 17
    XDR_OPERATION_TYPE_REVOKE_SPONSORSHIP = 18
    XDR_OPERATION_TYPE_CLAWBACK = 19
    XDR_OPERATION_TYPE_CLAWBACK_CLAIMABLE_BALANCE = 20
    XDR_OPERATION_TYPE_SET_TRUST_LINE_FLAGS = 21
    XDR_OPERATION_TYPE_LIQUIDITY_POOL_DEPOSIT = 22
    XDR_OPERATION_TYPE_LIQUIDITY_POOL_WITHDRAW = 23

class AssetType(IntEnum):
    ASSET_TYPE_NATIVE = 0
    ASSET_TYPE_CREDIT_ALPHANUM4 = 1
    ASSET_TYPE_CREDIT_ALPHANUM12 = 2
    ASSET_TYPE_POOL_SHARE = 3


def _format_memo_text(memo: str) -> bytes:
    memo_bytes = memo.encode()
    memo_len = len(memo_bytes)
    padding_length = memo_len % 4
    if padding_length == 0:
        padding = b""
    else:
        padding = b'\x00' * (4 - padding_length)
    return int.to_bytes(memo_len, length=4, byteorder='big') + memo_bytes + padding


class StellarErrors(IntEnum):
    SW_DENY = 0x6985

class StellarClient:
    CLA = 0xE0

    def __init__(self, backend):
        self._backend = backend

    def _craft_simple_tx(self, network: Network, fees: int, memo: str, destination: str, send_amount: int) -> bytes:
        tx: bytes = b""
        tx += networks_dict[network]
        tx += int.to_bytes(EnvelopeType.ENVELOPE_TYPE_TX, length=4, byteorder='big')
        tx += int.to_bytes(CryptoKeyType.KEY_TYPE_ED25519, length=4, byteorder='big')
        tx += StrKey.decode_ed25519_public_key("GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B")
        tx += int.to_bytes(fees, length=4, byteorder='big')
        tx += bytes.fromhex("0123 4567 89AB CDEF") # sequence number
        tx += int.to_bytes(PreconditionType.PRECOND_NONE, length=4, byteorder='big')
        tx += int.to_bytes(MemoType.MEMO_TEXT, length=4, byteorder='big')
        tx += _format_memo_text(memo)
        tx += int.to_bytes(1, length=4, byteorder='big') # opcount
        tx += int.to_bytes(False, length=4, byteorder='big') # optional type not present
        tx += int.to_bytes(XDROperationType.XDR_OPERATION_TYPE_PAYMENT, length=4, byteorder='big')
        tx += int.to_bytes(CryptoKeyType.KEY_TYPE_ED25519, length=4, byteorder='big')
        tx += StrKey.decode_ed25519_public_key(destination)
        tx += int.to_bytes(AssetType.ASSET_TYPE_NATIVE, length=4, byteorder='big')
        tx += int.to_bytes(send_amount, length=8, byteorder='big')
        return tx

    def send_simple_sign_tx(self, path:str, network: Network, fees: int, memo: str, destination: str, send_amount: int) -> RAPDU:
        packed_path = pack_derivation_path(path)
        tx = self._craft_simple_tx(network=network, fees=fees, memo=memo, destination=destination, send_amount=send_amount)
        return self._backend.exchange(self.CLA, Ins.SIGN, P1.FIRST, P2.LAST, packed_path + tx)



