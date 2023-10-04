import traceback
from enum import IntEnum

from nacl.encoding import HexEncoder
from nacl.signing import VerifyKey,SigningKey
from nacl.exceptions import BadSignatureError

from ragger.utils import create_currency_config
from ragger.bip import bitcoin_pack_derivation_path, BtcDerivationPathFormat
from ragger.error import ExceptionRAPDU
from scalecodec.base import RuntimeConfiguration
from scalecodec.type_registry import load_type_registry_preset
from scalecodec.utils.ss58 import ss58_decode

class Method(IntEnum):
    BALANCE_TRANSFER = 0x0500
    BALANCE_FORCE_TRANSFER = 0x0502

class AccountIdLookupType(IntEnum):
    ID = 0
    INDEX = 1
    RAW = 2
    ADDRESS32 = 3
    ADDRESS20 = 4

def _polkadot_address_to_pk(address: str) -> bytes:
    return bytes.fromhex(ss58_decode(address))

def _format_amount(amount: int) -> bytes:
    RuntimeConfiguration().update_type_registry(load_type_registry_preset("legacy"))
    obj = RuntimeConfiguration().create_scale_object('Compact<Balance>')
    scale_data = obj.encode(amount)
    return bytes(scale_data.get_remaining_bytes())

# Not sure what this exactly is but we don't actually care
UNKNOWN = bytes([0x85, 0x02, 0x00, 0x00])

SPEC_VERSION = 9360
TX_VERSION = 24

# We don't care about the block hash content
BLOCK_HASH = bytes([0x00] * 32)

GENESIS_HASH = bytes([
    0x91, 0xb1, 0x71, 0xbb, 0x15, 0x8e, 0x2d, 0x38, 0x48, 0xfa,
    0x23, 0xa9, 0xf1, 0xc2, 0x51, 0x82, 0xfb, 0x8e, 0x20, 0x31,
    0x3b, 0x2c, 0x1e, 0xb4, 0x92, 0x19, 0xda, 0x7a, 0x70, 0xce,
    0x90, 0xc3,
])

ERR_SWAP_CHECK_WRONG_METHOD = 0x6984
ERR_SWAP_CHECK_WRONG_METHOD_ARGS_CNT = 0x6984
ERR_SWAP_CHECK_WRONG_DEST_ADDR = 0x6984
ERR_SWAP_CHECK_WRONG_AMOUNT = 0x6984

class Command:
    GET_VERSION = 0x00
    GET_ADDRESS = 0x01
    SIGN_TX = 0x02

class GetAddrP1:
    NO_CONFIRM = 0x00
    CONFIRM = 0x01

class SignP1:
    INIT = 0x00
    ADD = 0x01
    LAST = 0x02

class SignP2Last:
    ED25519 = 0x00
    SR25119 = 0x01

DOT_CONF = create_currency_config("DOT", "Polkadot", ("DOT", 18))

DOT_PACKED_DERIVATION_PATH = bitcoin_pack_derivation_path(BtcDerivationPathFormat.LEGACY, "m/44'/354'/0'/0'/0'")

DOT_PACKED_DERIVATION_PATH_SIGN_INIT = bytes([0x2c, 0x00, 0x00, 0x80,
                                              0x62, 0x01, 0x00, 0x80,
                                              0x00, 0x00, 0x00, 0x80,
                                              0x00, 0x00, 0x00, 0x80,
                                              0x00, 0x00, 0x00, 0x80])


class PolkadotClient:
    CLA = 0x90
    def __init__(self, client):
        self._client = client

    @property
    def client(self):
        return self._client

    def get_pubkey(self):
        msg = self.client.exchange(self.CLA, ins=Command.GET_ADDRESS, p1=0, p2=0, data=DOT_PACKED_DERIVATION_PATH_SIGN_INIT)
        return msg.data[:32].hex().encode()

    def sign_init(self):
        return self.client.exchange(self.CLA, ins=Command.SIGN_TX, p1=SignP1.INIT, data=DOT_PACKED_DERIVATION_PATH_SIGN_INIT)

    def sign_add(self,tx_chunk):
        return self.client.exchange(self.CLA, ins=Command.SIGN_TX, p1=SignP1.ADD,data=tx_chunk)

    def sign_last(self,tx_chunk):
        return self.client.exchange(self.CLA, ins=Command.SIGN_TX, p1=SignP1.LAST, p2=SignP2Last.ED25519, data=tx_chunk)

    def verify_signature(self,hex_key:bytes,signature:bytes,message:bytes) -> bool :
        # Create a VerifyKey object from a hex serialized public key
        verify_key = VerifyKey(hex_key, encoder=HexEncoder)
        # Check the validity of a message's signature
        try:
            verify_key.verify(message, signature, encoder=HexEncoder)
        except BadSignatureError:
            print("Wrong signature.")
            return False
        except Exception as e :
            print("Something went wrong.")
            print(e)
            print(traceback.format_exc())
            return False
        else:
            print("Signature is ok.")
            return True

    def craft_valid_polkadot_transaction(address, send_amount, fees, memo) -> bytes:
        return Method.BALANCE_TRANSFER.to_bytes(2, "big") \
               + AccountIdLookupType.ID.to_bytes(1, "big") \
               + _polkadot_address_to_pk(address) \
               + _format_amount(send_amount) \
               + UNKNOWN \
               + SPEC_VERSION.to_bytes(4, "little") \
               + TX_VERSION.to_bytes(4, "little") \
               + GENESIS_HASH \
               + BLOCK_HASH

    def craft_invalid_polkadot_transaction(address, send_amount, fees, memo) -> bytes:
        force_transfer = Method.BALANCE_FORCE_TRANSFER.to_bytes(2, "big") \
                       + bytes([0x00, 0xdc, 0x5a, 0xda, 0x10, 0xee, 0xdd, 0x89, 0x81, 0x92,
                                0x78, 0xb0, 0x92, 0x35, 0x87, 0x80, 0x3d, 0x7d, 0xb2, 0x07,
                                0xe1, 0xdc, 0x7e, 0x1c, 0x18, 0x42, 0x4f, 0xa4, 0xad, 0x59,
                                0xb4, 0x00, 0x19, 0x00, 0xb0, 0x0b, 0x9f, 0x27, 0xc2, 0xd1,
                                0xd2, 0x16, 0x01, 0x58, 0x51, 0xdc, 0x3a, 0x69, 0xc8, 0xab,
                                0x52, 0xb2, 0x86, 0x62, 0xe7, 0xfa, 0x31, 0x7c, 0x07, 0xad,
                                0x1f, 0x34, 0xa4, 0xdf, 0xcd, 0x62, 0x07, 0x70, 0xf9, 0xdb,
                                0xdf, 0x02, 0x55, 0x02, 0x00, 0x00])

        return force_transfer \
               + SPEC_VERSION.to_bytes(4, "little") \
               + TX_VERSION.to_bytes(4, "little") \
               + GENESIS_HASH \
               + BLOCK_HASH
