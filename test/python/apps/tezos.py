from enum import IntEnum, Enum, auto
from typing import List, Generator
from contextlib import contextmanager

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config, RAPDU

XTZ_CONF = create_currency_config("XTZ", "Tezos")

XTZ_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/1729'/0'")

# TEZ_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/1729'/0'/0'")
# CLA = 0x80

# CMD_PART1 = "17777d8de5596705f1cb35b0247b9605a7c93a7ed5c0caa454d4f4ff39eb411d"

# CMD_PART2 = "00cf49f66b9ea137e11818f2a78b4b6fc9895b4e50830ae58003c35000c0843d0000eac6c762212c4110f221ec8fcb05ce83db95845700"


# class INS(IntEnum):
#     INS_VERSION = 0x00
#     INS_GET_PUBLIC_KEY = 0x02
#     INS_QUERY_AUTH_KEY = 0x07
#     INS_QUERY_MAIN_HWM = 0x08
#     INS_GIT = 0x09
#     INS_QUERY_ALL_HWM = 0x0b
#     INS_DEAUTHORIZE = 0x0c
#     INS_QUERY_AUTH_KEY_WITH_CURVE = 0x0d
#     INS_HMAC = 0x0e
#     INS_AUTHORIZE_BAKING = 0x01
#     INS_PROMPT_PUBLIC_KEY = 0x03
#     INS_SIGN = 0x04
#     INS_SIGN_UNSAFE = 0x05
#     INS_RESET = 0x06
#     INS_SETUP = 0x0a
#     INS_SIGN_WITH_HASH = 0x0f


# class P1(IntEnum):
#     FIRST = 0x00
#     OTHER = 0x01
#     LAST = 0x81


# class P2(IntEnum):
#     ED25519 = 0x00
#     SECP256K1 = 0x01
#     SECP256R1 = 0x02
#     BIPs32_ED25519 = 0x03


# class OPERATION_TAG(IntEnum):
#     OPERATION_TAG_PROPOSAL = 5,
#     OPERATION_TAG_BALLOT = 6,
#     OPERATION_TAG_BABYLON_REVEAL = 107,
#     OPERATION_TAG_BABYLON_TRANSACTION = 108,
#     OPERATION_TAG_BABYLON_ORIGINATION = 109,
#     OPERATION_TAG_BABYLON_DELEGATION = 110,
#     OPERATION_TAG_ATHENS_REVEAL = 7,
#     OPERATION_TAG_ATHENS_TRANSACTION = 8,
#     OPERATION_TAG_ATHENS_ORIGINATION = 9,
#     OPERATION_TAG_ATHENS_DELEGATION = 10


# class MAGICBYTE(IntEnum):
#     BLOCK = 0x01
#     UNSAFE = 0x03


# class StatusCode(IntEnum):
#     STATUS_OK = 0x9000


# class TezosClient:
#     backend: BackendInterface

#     def __init__(self, backend):
#         self._client = backend

#     @contextmanager
#     def authorize_baking(self, derivation_path: bytes) -> Generator[None, None, None]:
#         with self._client.exchange_async(CLA,
#                                          INS.INS_AUTHORIZE_BAKING,
#                                          P1.FIRST,
#                                          P2.ED25519,
#                                          derivation_path):
#             yield

#     @contextmanager
#     def get_public_key_silent(self, derivation_path: bytes) -> Generator[None, None, None]:
#         with self._client.exchange_async(CLA,
#                                          INS.INS_GET_PUBLIC_KEY,
#                                          P1.FIRST,
#                                          P2.ED25519,
#                                          derivation_path):
#             yield

#     @contextmanager
#     def get_public_key_prompt(self, derivation_path: bytes) -> Generator[None, None, None]:
#         with self._client.exchange_async(CLA,
#                                          INS.INS_PROMPT_PUBLIC_KEY,
#                                          P1.FIRST,
#                                          P2.ED25519,
#                                          derivation_path):
#             yield

#     @contextmanager
#     def reset_app_context(self, reset_level: int) -> Generator[None, None, None]:
#         with self._client.exchange_async(CLA,
#                                          INS.INS_RESET,
#                                          P1.LAST,
#                                          P2.ED25519,
#                                          reset_level.to_bytes(4, byteorder='big')):
#             yield

#     @contextmanager
#     def setup_baking_address(self, derivation_path: bytes, chain: int, main_hwm: int, test_hwm: int) -> Generator[None, None, None]:

#         data: bytes = chain.to_bytes(4, byteorder='big') + main_hwm.to_bytes(
#             4, byteorder='big') + test_hwm.to_bytes(4, byteorder='big') + derivation_path

#         with self._client.exchange_async(CLA,
#                                          INS.INS_SETUP,
#                                          P1.FIRST,
#                                          P2.ED25519,
#                                          data):
#             yield

#     @contextmanager
#     def sign_message(self, derivation_path: bytes, operation_tag: OPERATION_TAG) -> Generator[None, None, None]:

#         self._client.exchange(CLA,
#                               INS.INS_SIGN,
#                               P1.FIRST,
#                               P2.BIPs32_ED25519,
#                               derivation_path)

#         data: bytes = bytes.fromhex(
#             CMD_PART1) + operation_tag.to_bytes(1, byteorder='big') + bytes.fromhex(CMD_PART2)

#         with self._client.exchange_async(CLA,
#                                          INS.INS_SIGN,
#                                          P1.LAST,
#                                          P2.ED25519,
#                                          MAGICBYTE.UNSAFE.to_bytes(1, byteorder='big') + data):
#             yield

#     @contextmanager
#     def sign_message_exchange(self, derivation_path: bytes = XTZ_PACKED_DERIVATION_PATH) -> Generator[None, None, None]:

#         rapdu = self._client.exchange(CLA,
#                               INS.INS_SIGN,
#                               P1.FIRST,
#                               P2.BIPs32_ED25519,
#                               derivation_path)
#         print("P1 done")
#         data: bytes = bytes.fromhex(
#             CMD_PART1) + OPERATION_TAG.OPERATION_TAG_BABYLON_TRANSACTION.to_bytes(1, byteorder='big') + bytes.fromhex(CMD_PART2)

#         self._client.exchange(CLA,
#                               INS.INS_SIGN,
#                               P1.LAST,
#                               P2.ED25519,
#                               MAGICBYTE.UNSAFE.to_bytes(1, byteorder='big') + data)

#     def get_async_response(self) -> RAPDU:
#         return self._client.last_async_response
