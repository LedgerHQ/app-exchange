import struct

from enum import IntEnum, Enum, auto
from typing import List, Generator
from contextlib import contextmanager
from hashlib import blake2b, sha256
from base58 import b58encode
from pathlib import Path
from .exchange_navigation_helper import ExchangeNavigationHelper, ROOT_SCREENSHOT_PATH

from ragger.navigator import Navigator, NavIns, NavInsID
from ragger.backend.interface import BackendInterface, RAPDU
from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config, RAPDU


NTZ_CONF = create_currency_config("NTZ", "Tezos Wallet", ("TZ", 6))

NTZ_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/1729'/0'")

HASH_SIZE = 20

HEADER_SIZE = 5
MAX_APDU_SIZE = 235
MAX_PAYLOAD_SIZE = MAX_APDU_SIZE - HEADER_SIZE


#################### APDU ####################

class CLA(IntEnum):
    DEFAULT = 0x80

class INS(IntEnum):
    VERSION                   = 0x00
    AUTHORIZE_BAKING          = 0x01
    GET_PUBLIC_KEY            = 0x02
    PROMPT_PUBLIC_KEY         = 0x03
    SIGN                      = 0x04
    SIGN_UNSAFE               = 0x05
    RESET                     = 0x06
    QUERY_AUTH_KEY            = 0x07
    QUERY_MAIN_HWM            = 0x08
    GIT                       = 0x09
    SETUP                     = 0x0a
    QUERY_ALL_HWM             = 0x0b
    DEAUTHORIZE               = 0x0c
    QUERY_AUTH_KEY_WITH_CURVE = 0x0d
    HMAC                      = 0x0e
    SIGN_WITH_HASH            = 0x0f

class INDEX(IntEnum):
    FIRST = 0x00
    OTHER = 0x01
    LAST = 0x81

# P1 is used to transmit the packet index, alias it
P1 = INDEX

class SIGNATURE_TYPE(IntEnum):
    ED25519       = 0x00
    SECP256K1     = 0x01
    SECP256R1     = 0x02
    BIP32_ED25519 = 0x03

# P2 is used to transmit the signature type, alias it
P2 = SIGNATURE_TYPE

class StatusCode(IntEnum):
    STATUS_OK = 0x9000
    EXC_REJECT = 0x6985


################# MESSAGE ##################

class MAGIC_BYTE(IntEnum):
    OPERATION = 0x03
    MICHELINE = 0x05

class OPERATION_TAG(IntEnum):
    PROPOSALS    =   5,
    BALLOT       =   6,
    FAILING_NOOP =  17,
    REVEAL       = 107,
    TRANSACTION  = 108,
    ORIGINATION  = 109,
    DELEGATION   = 110,
    REG_GLB_CST  = 111,
    SET_DEPOSIT  = 112,
    INC_PAID_STG = 113,
    UPDATE_CK    = 114,
    TRANSFER_TCK = 158,
    SORU_ORIGIN  = 200,
    SORU_ADD_MSG = 201,
    SORU_EXE_MSG = 206

class CONTRACT_TYPE(IntEnum):
    IMPLICIT = 0x00
    ORIGINATED = 0x01

def zeros_bytes(size: int) -> bytes:
    zero = bytes.fromhex("00")
    result = b""
    for i in range(size):
        result += zero
    return result

def encode_address(blake2_hashed_pubkey: str) -> bytes:
    P2HASH_MAGIC = bytes.fromhex('06a19f')
    blake2bhash = bytes.fromhex(blake2_hashed_pubkey)
    shabytes = sha256(sha256(P2HASH_MAGIC + blake2bhash).digest()).digest()[:4]
    pkhash = b58encode(P2HASH_MAGIC + blake2bhash + shabytes).decode()
    return pkhash

def blake2_hash_pubkey(pubkey: bytes) -> bytes:
    return blake2b(pubkey, digest_size=HASH_SIZE).digest()

def pkh_to_bytes(pkh: bytes, signature_type: SIGNATURE_TYPE) -> bytes:

    result = b""

    result += signature_type.to_bytes(1, byteorder='big')
    result += pkh

    return result

def contract_to_bytes(contract: str, contract_type: CONTRACT_TYPE) -> bytes:

    result = b""

    result += contract_type.to_bytes(1, byteorder='big')
    if contract_type == CONTRACT_TYPE.IMPLICIT:
        result += zeros_bytes(1) # need one padding
    result += bytes.fromhex(contract)

    return result

# Weird Tezos formating used for values:
# Values are packed on the 7 week bits of each byte
# The strongest bit is set to true if the value is over
# Example with format(300):
# First byte is  ((300 >> 0) & 0x7F) | 0x80
# Second byte is ((300 >> 7) & 0x7F)
def tezos_format_z_pack(value: int) -> bytes:
    if value == 0:
        return int.to_bytes(0, length=1, byteorder='big')

    ret = b""
    current_offset = 0
    while (value >> current_offset) != 0:
        current_value = ((value >> current_offset) & 0x7F)
        current_offset += 7
        if (value >> current_offset) != 0:
            current_value |= 0x80
        ret += int.to_bytes(current_value, length=1, byteorder='big')
    return ret


class TezosClient:

    def __init__(self, backend: BackendInterface, exchange_navigation_helper: ExchangeNavigationHelper, signature_type: SIGNATURE_TYPE):
        self._backend = backend
        self._exchange_navigation_helper = exchange_navigation_helper
        self.signature_type = signature_type

    def _exchange(self, ins: INS, index: INDEX, payload: bytes = b"") -> RAPDU:
        return self._backend.exchange(CLA.DEFAULT,
                                      ins,
                                      p1=index,
                                      p2=self.signature_type,
                                      data=payload)

    @contextmanager
    def _exchange_async(self, ins: INS, index: INDEX, payload: bytes = b"") -> Generator[None, None, None]:
        with self._backend.exchange_async(CLA.DEFAULT,
                                          ins,
                                          p1=index,
                                          p2=self.signature_type,
                                          data=payload):
            yield

    def get_public_key(self) -> RAPDU:
        return self._exchange(INS.GET_PUBLIC_KEY, P1.FIRST, payload=NTZ_PACKED_DERIVATION_PATH)

    def sign_message(self, ins: INS = INS.SIGN_WITH_HASH, message: bytes = b"") -> RAPDU:

        # todo: send the message by chunk instead of fail
        assert len(message) <= MAX_PAYLOAD_SIZE, "Message to send is too long"

        first_rapdu = self._exchange(ins, P1.FIRST, NTZ_PACKED_DERIVATION_PATH)
        if first_rapdu.status != StatusCode.STATUS_OK:
            return first_rapdu

        with self._exchange_async(ins, index=INDEX.LAST, payload=message):
            snapshots_dir_name = self._exchange_navigation_helper.snapshots_dir_name + "/signing"
            validation_instructions : list[NavIns | NavInsID] = []
            if self._backend.firmware.is_nano:
                navigate_instruction = NavInsID.RIGHT_CLICK
                validation_instructions = [NavInsID.BOTH_CLICK]
            else:
                navigate_instruction = NavInsID.USE_CASE_REVIEW_TAP
                validation_instructions = [NavInsID.USE_CASE_REVIEW_CONFIRM]
            text="Accept"
            self._exchange_navigation_helper.\
                _navigator.\
                navigate_until_text_and_compare(navigate_instruction,
                                                validation_instructions,
                                                text,
                                                path=ROOT_SCREENSHOT_PATH,
                                                test_case_name=Path(snapshots_dir_name),
                                                screen_change_before_first_instruction=False)

        rapdu = self._backend.last_async_response
        assert rapdu is not None
        return rapdu

    # Simple TX used for Exchange tests
    def _craft_simple_tx(self,
                         source: bytes,
                         source_signature_type: SIGNATURE_TYPE,
                         fee: int,
                         destination: str,
                         amount: int) -> bytes:

        payload = b""

        payload += MAGIC_BYTE.OPERATION.to_bytes(1, byteorder='big')
        payload += zeros_bytes(32) # block hash, ignored
        payload += OPERATION_TAG.TRANSACTION.to_bytes(1, byteorder='big')
        payload += pkh_to_bytes(blake2_hash_pubkey(source), source_signature_type)
        payload += tezos_format_z_pack(fee)
        payload += zeros_bytes(1) # counter = 0
        payload += zeros_bytes(1) # gas limit = 0
        payload += zeros_bytes(1) # storage limit = 0
        payload += tezos_format_z_pack(amount)
        payload += contract_to_bytes(destination, CONTRACT_TYPE.IMPLICIT)
        payload += zeros_bytes(1) # parameters = none

        return payload

    def send_simple_sign_tx(self, fee: int, destination: str, amount: int) -> RAPDU:

        rapdu = self.get_public_key()
        if rapdu.status != StatusCode.STATUS_OK:
                return rapdu

        response_len, _, source = struct.unpack('<BB32s', rapdu.data)
        assert response_len == len(rapdu.data) - 1

        # Perform the actual signing
        tx = self._craft_simple_tx(source, self.signature_type, fee, destination, amount)
        rapdu = self.sign_message(message=tx)
        return rapdu
