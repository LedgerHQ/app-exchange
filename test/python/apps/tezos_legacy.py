import struct

from enum import IntEnum, Enum, auto
from typing import List, Generator
from contextlib import contextmanager
from hashlib import blake2b, sha256
from base58 import b58encode

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config, RAPDU

XTZ_CONF = create_currency_config("XTZ", "Tezos")

XTZ_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/1729'/0'")

CMD_PART1 = "17777d8de5596705f1cb35b0247b9605a7c93a7ed5c0caa454d4f4ff39eb411d"

CMD_PART2 = "00cf49f66b9ea137e11818f2a78b4b6fc9895b4e50830ae58003c35000c0843d0000eac6c762212c4110f221ec8fcb05ce83db95845700"

HASH_SIZE = 20

class INS(IntEnum):
    INS_VERSION = 0x00
    INS_GET_PUBLIC_KEY = 0x02
    INS_QUERY_AUTH_KEY = 0x07
    INS_QUERY_MAIN_HWM = 0x08
    INS_GIT = 0x09
    INS_QUERY_ALL_HWM = 0x0b
    INS_DEAUTHORIZE = 0x0c
    INS_QUERY_AUTH_KEY_WITH_CURVE = 0x0d
    INS_HMAC = 0x0e
    INS_AUTHORIZE_BAKING = 0x01
    INS_PROMPT_PUBLIC_KEY = 0x03
    INS_SIGN = 0x04
    INS_SIGN_UNSAFE = 0x05
    INS_RESET = 0x06
    INS_SETUP = 0x0a
    INS_SIGN_WITH_HASH = 0x0f


class P1(IntEnum):
    FIRST = 0x00
    OTHER = 0x01
    LAST = 0x81


class SIGNATURE_TYPE(IntEnum):
    ED25519 = 0x00
    SECP256K1 = 0x01
    SECP256R1 = 0x02
    BIPs32_ED25519 = 0x03


# P2 is used to transmit the signature type, alias it
P2 = SIGNATURE_TYPE


class CONTRACT_TYPE(IntEnum):
    IMPLICIT = 0x00
    ORIGINATED = 0x01


class OPERATION_TAG(IntEnum):
    OPERATION_TAG_PROPOSAL = 5,
    OPERATION_TAG_BALLOT = 6,
    OPERATION_TAG_BABYLON_REVEAL = 107,
    OPERATION_TAG_BABYLON_TRANSACTION = 108,
    OPERATION_TAG_BABYLON_ORIGINATION = 109,
    OPERATION_TAG_BABYLON_DELEGATION = 110,
    OPERATION_TAG_ATHENS_REVEAL = 7,
    OPERATION_TAG_ATHENS_TRANSACTION = 8,
    OPERATION_TAG_ATHENS_ORIGINATION = 9,
    OPERATION_TAG_ATHENS_DELEGATION = 10


class MAGICBYTE(IntEnum):
    BLOCK = 0x01
    UNSAFE = 0x03

class MICHELSON_PARAMS_TAG(IntEnum):
    NONE = 0x00
    SOME = 0xff

class StatusCode(IntEnum):
    STATUS_OK = 0x9000
    EXC_REJECT = 0x6985


def encode_address(blake2_hashed_pubkey: str) -> bytes:
    P2HASH_MAGIC = bytes.fromhex('06a19f')
    blake2bhash = bytes.fromhex(blake2_hashed_pubkey)
    shabytes = sha256(sha256(P2HASH_MAGIC + blake2bhash).digest()).digest()[:4]
    pkhash = b58encode(P2HASH_MAGIC + blake2bhash + shabytes).decode()
    return pkhash


def blake2_hash_pubkey(pubkey: bytes) -> bytes:
    return blake2b(pubkey, digest_size=HASH_SIZE).digest()


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
    CLA = 0x80

    def __init__(self, backend):
        self._backend = backend

    @contextmanager
    def authorize_baking(self, derivation_path: bytes) -> Generator[None, None, None]:
        with self._backend.exchange_async(self.CLA,
                                         INS.INS_AUTHORIZE_BAKING,
                                         P1.FIRST,
                                         P2.ED25519,
                                         derivation_path):
            yield

    def get_public_key_silent(self, derivation_path: bytes) -> RAPDU:
        rapdu = self._backend.exchange(self.CLA,
                                       INS.INS_GET_PUBLIC_KEY,
                                       P1.FIRST,
                                       P2.ED25519,
                                       derivation_path)
        return rapdu

    @contextmanager
    def get_public_key_prompt(self, derivation_path: bytes) -> Generator[None, None, None]:
        with self._backend.exchange_async(self.CLA,
                                         INS.INS_PROMPT_PUBLIC_KEY,
                                         P1.FIRST,
                                         P2.ED25519,
                                         derivation_path):
            yield

    @contextmanager
    def reset_app_context(self, reset_level: int) -> Generator[None, None, None]:
        with self._backend.exchange_async(self.CLA,
                                         INS.INS_RESET,
                                         P1.LAST,
                                         P2.ED25519,
                                         reset_level.to_bytes(4, byteorder='big')):
            yield

    @contextmanager
    def setup_baking_address(self, derivation_path: bytes, chain: int, main_hwm: int, test_hwm: int) -> Generator[None, None, None]:

        data: bytes = chain.to_bytes(4, byteorder='big') + main_hwm.to_bytes(
            4, byteorder='big') + test_hwm.to_bytes(4, byteorder='big') + derivation_path

        with self._backend.exchange_async(self.CLA,
                                         INS.INS_SETUP,
                                         P1.FIRST,
                                         P2.ED25519,
                                         data):
            yield

    @contextmanager
    def sign_message(self, derivation_path: bytes, operation_tag: OPERATION_TAG) -> Generator[None, None, None]:

        self._backend.exchange(self.CLA,
                              INS.INS_SIGN,
                              P1.FIRST,
                              P2.BIPs32_ED25519,
                              derivation_path)

        data: bytes = bytes.fromhex(
            CMD_PART1) + operation_tag.to_bytes(1, byteorder='big') + bytes.fromhex(CMD_PART2)

        with self._backend.exchange_async(self.CLA,
                                         INS.INS_SIGN,
                                         P1.LAST,
                                         P2.ED25519,
                                         MAGICBYTE.UNSAFE.to_bytes(1, byteorder='big') + data):
            yield

    def get_async_response(self) -> RAPDU:
        return self._backend.last_async_response

    # Simple TX used for Exchange tests
    def _craft_simple_tx(self, device_pk: bytes, fees: int, memo: str, destination: str, send_amount: int) -> bytes:
        hashed_pubkey = blake2_hash_pubkey(device_pk)
        payload = b""

        # Header
        payload += MAGICBYTE.UNSAFE.to_bytes(1, byteorder='big') # operation_group_header magic byte 0x3
        payload += bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000") # block hash, ignored

        # Operation 1 OPERATION_TAG_BABYLON_REVEAL
        payload += OPERATION_TAG.OPERATION_TAG_BABYLON_REVEAL.to_bytes(1, byteorder='big')
        payload += SIGNATURE_TYPE.ED25519.to_bytes(1, byteorder='big')
        payload += hashed_pubkey # operation source hash
        payload += tezos_format_z_pack(0) # operation 1 fees
        payload += bytes.fromhex("00") # counter
        payload += bytes.fromhex("00") # gas limit
        payload += bytes.fromhex("00") # storage limit
        payload += SIGNATURE_TYPE.ED25519.to_bytes(1, byteorder='big')
        payload += device_pk # pubkey of the device

        # Operation 2 OPERATION_TAG_BABYLON_TRANSACTION
        payload += OPERATION_TAG.OPERATION_TAG_BABYLON_TRANSACTION.to_bytes(1, byteorder='big')
        payload += SIGNATURE_TYPE.ED25519.to_bytes(1, byteorder='big')
        payload += hashed_pubkey # operation source hash
        payload += tezos_format_z_pack(fees) # operation 2 fees
        payload += bytes.fromhex("00") # counter
        payload += bytes.fromhex("00") # gas limit
        payload += bytes.fromhex("00") # storage limit
        payload += tezos_format_z_pack(send_amount) # amount
        payload += CONTRACT_TYPE.IMPLICIT.to_bytes(1, byteorder='big') # not originated contract
        payload += SIGNATURE_TYPE.ED25519.to_bytes(1, byteorder='big')
        payload += bytes.fromhex(destination) # destination address
        payload += MICHELSON_PARAMS_TAG.NONE.to_bytes(1, byteorder='big')

        return payload

    def send_simple_sign_tx(self, path: str, fees: int, memo: str, destination: str, send_amount: int) -> RAPDU:
    	# First get the device public key, we'll need it
        rapdu = self.get_public_key_silent(path)
        if rapdu.status != StatusCode.STATUS_OK:
        	return rapdu

        response_len, _, device_pk = struct.unpack('<BB32s', rapdu.data)
        assert response_len == len(rapdu.data) - 1

    	# Init a Sign on the derivation path
        rapdu = self._backend.exchange(self.CLA, INS.INS_SIGN, P1.FIRST, P2.ED25519, XTZ_PACKED_DERIVATION_PATH)
        if rapdu.status != StatusCode.STATUS_OK:
        	return rapdu

    	# Perform the actual signing
        payload = self._craft_simple_tx(device_pk, fees, memo, destination, send_amount)
        rapdu = self._backend.exchange(self.CLA,
									   INS.INS_SIGN,
									   P1.LAST,
									   P2.ED25519,
									   data=payload)
        return rapdu
