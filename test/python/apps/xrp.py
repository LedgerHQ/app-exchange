#!/usr/bin/env python3

from typing import Generator
from contextlib import contextmanager
from enum import IntEnum
from time import sleep
from ragger.backend.interface import BackendInterface, RAPDU
from ragger.navigator import NavInsID, NavIns
import pathlib

from ecdsa.util import sigdecode_der
from ecdsa import VerifyingKey, SECP256k1
from hashlib import sha256

from ragger.utils import create_currency_config
from ragger.bip import pack_derivation_path

from xrpl.core import addresscodec


### Proposed Solana derivation paths for tests ###
XRP_DEFAULT_PATH = "44'/144'/0'/0/0"
XRP_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/144'/0'/0/0")


### Package this currency configuration in exchange format ###

XRP_CONF = create_currency_config("XRP", "XRP")


class Ins(IntEnum):
    GET_PUBLIC_KEY = 0x02
    SIGN = 0x04


class P1(IntEnum):
    NON_CONFIRM = 0x00
    CONFIRM = 0x01
    FIRST = 0x00
    NEXT = 0x01
    ONLY = 0x00
    MORE = 0x80
    INTER = 0x81


class P2(IntEnum):
    NO_CHAIN_CODE = 0x00
    CHAIN_CODE = 0x01
    CURVE_SECP256K1 = 0x40
    CURVE_ED25519 = 0x80

class TRANSACTION_TYPE(IntEnum):
    TRANSACTION_PAYMENT = 0
    TRANSACTION_ESCROW_CREATE = 1
    TRANSACTION_ESCROW_FINISH = 2
    TRANSACTION_ACCOUNT_SET = 3
    TRANSACTION_ESCROW_CANCEL = 4
    TRANSACTION_SET_REGULAR_KEY = 5
    TRANSACTION_OFFER_CREATE = 7
    TRANSACTION_OFFER_CANCEL = 8
    TRANSACTION_SIGNER_LIST_SET = 12
    TRANSACTION_PAYMENT_CHANNEL_CREATE = 13
    TRANSACTION_PAYMENT_CHANNEL_FUND = 14
    TRANSACTION_PAYMENT_CHANNEL_CLAIM = 15
    TRANSACTION_CHECK_CREATE = 16
    TRANSACTION_CHECK_CASH = 17
    TRANSACTION_CHECK_CANCEL = 18
    TRANSACTION_DEPOSIT_PREAUTH = 19
    TRANSACTION_TRUST_SET = 20
    TRANSACTION_ACCOUNT_DELETE = 21

class STI_FIELDS(IntEnum):
    # Normal field types
    STI_UINT16 = 0x01,
    STI_UINT32 = 0x02,
    STI_HASH128 = 0x04,
    STI_HASH256 = 0x05,
    STI_AMOUNT = 0x06,
    STI_VL = 0x07,
    STI_ACCOUNT = 0x08,
    STI_OBJECT = 0x0E,
    STI_ARRAY = 0x0F,
    STI_UINT8 = 0x10,
    STI_PATHSET = 0x12,

    # Custom field types
    STI_CURRENCY = 0xF0,

# Small collection of used field IDs
class FIELDS_IDS(IntEnum):
    XRP_UINT16_TRANSACTION_TYPE = 0x02
    XRP_UINT32_FLAGS = 0x02
    XRP_UINT32_SEQUENCE = 0x04
    XRP_UINT32_EXPIRATION = 0x0A
    XRP_UINT32_TRANSFER_RATE = 0x0B
    XRP_UINT32_QUALITY_IN = 0x14
    XRP_UINT32_QUALITY_OUT = 0x15
    XRP_UINT32_LAST_LEDGER_SEQUENCE = 0x1B
    XRP_UINT32_SET_FLAG = 0x21
    XRP_UINT32_CLEAR_FLAG = 0x22
    XRP_UINT32_CANCEL_AFTER = 0x24
    XRP_UINT32_FINISH_AFTER = 0x25
    XRP_UINT32_SETTLE_DELAY = 0x27
    XRP_VL_SIGNING_PUB_KEY = 0x03
    XRP_VL_DOMAIN = 0x07
    XRP_VL_MEMO_TYPE = 0x0C
    XRP_VL_MEMO_DATA = 0x0D
    XRP_VL_MEMO_FORMAT = 0x0E
    XRP_ACCOUNT_ACCOUNT = 0x01
    XRP_ACCOUNT_DESTINATION = 0x03
    XRP_ACCOUNT_ISSUER = 0x04
    XRP_ACCOUNT_REGULAR_KEY = 0x08
    XRP_CURRENCY_CURRENCY = 0x01
    XRP_UINT64_AMOUNT = 0x01
    XRP_UINT64_FEE = 0x08

TF_FULLY_CANONICAL_SIG = 0x80000000

XRP_ACCOUNT_SIZE = 20
XRP_CURRENCY_SIZE = 20

XRP_PUBKEY_SIZE = 33

class RippleErrors(IntEnum):
    SW_SWAP_CHECKING_FAIL = 0x6985

class Action(IntEnum):
    NAVIGATE = 0
    COMPARE = 1
    NONE = 2


DEFAULT_PATH = "44'/144'/0'/0'/0"


class XRPClient:
    CLA = 0xE0

    def __init__(self, backend: BackendInterface):
        if not isinstance(backend, BackendInterface):
            raise TypeError("backend must be an instance of BackendInterface")
        self._backend = backend

    def _exchange(self, ins: int, p1: int, p2: int, payload: bytes = b"") -> RAPDU:
        return self._backend.exchange(self.CLA, ins, p1=p1, p2=p2, data=payload)

    # Does not work :/
    def verify_ecdsa_secp256k1(self, msg, sig, pub_key):
        vk = VerifyingKey.from_string(
            pub_key, curve=SECP256k1, hashfunc=sha256, validate_point=False
        )
        return vk.verify(sig, msg, sha256, sigdecode=sigdecode_der)

    def get_pubkey(
        self, default_path: bool = True, confirm: bool = False, path: str = ""
    ):
        if confirm:
            p1 = P1.CONFIRM
        else:
            p1 = P1.NON_CONFIRM
        if default_path:
            my_path = Bip32Path.build(DEFAULT_PATH)
        else:
            my_path = path
        reply = self._exchange(
            Ins.GET_PUBLIC_KEY, p1=p1, p2=P2.CURVE_SECP256K1, payload=my_path
        )
        return reply.data[1 : reply.data[0]]

    @contextmanager
    def sign(self, payload, navigate: bool = False, snappath: str = ""):
        chunk_size = 255
        first = True
        while payload:
            if first:
                p1 = P1.FIRST
                first = False
            else:
                p1 = P1.NEXT

            size = min(len(payload), chunk_size)
            if size != len(payload):
                p1 |= P1.MORE

            p2 = P2.CURVE_SECP256K1

            if p1 in [P1.MORE, P1.INTER]:
                self._exchange(ins=Ins.SIGN, p1=p1, p2=p2, payload=payload[:size])
            elif p1 in [P1.FIRST, P1.NEXT]:
                with self._backend.exchange_async(
                    self.CLA, ins=Ins.SIGN, p1=p1, p2=p2, data=payload[:size]
                ) as r:
                    if navigate:
                        if not self._backend.firmware.is_nano:
                            sleep(1.5)
                            self._navigator.navigate_until_text_and_compare(
                                NavIns(NavInsID.USE_CASE_REVIEW_TAP),
                                [NavIns(NavInsID.USE_CASE_REVIEW_CONFIRM)],
                                "Hold to confirm",
                                pathlib.Path(__file__).parent.resolve(),
                                snappath,
                                screen_change_after_last_instruction=False,
                            )
                        else:
                            text_to_find = "Sign transaction"
                            if self._firmware.device == "nanox":
                                text_to_find = text_to_find[1:]
                            self._navigator.navigate_until_text_and_compare(
                                NavIns(NavInsID.RIGHT_CLICK),
                                [NavIns(NavInsID.BOTH_CLICK)],
                                text_to_find,
                                pathlib.Path(__file__).parent.resolve(),
                                snappath,
                                screen_change_after_last_instruction=False,
                            )
                    else:
                        pass
            payload = payload[size:]

    def _craft_simple_tx(self, fees: int, memo: str, destination: str, send_amount: int) -> bytes:
        tx: bytes = b""

        tx += int.to_bytes(STI_FIELDS.STI_UINT16 << 4 | FIELDS_IDS.XRP_UINT16_TRANSACTION_TYPE, length=1, byteorder='big')
        tx += int.to_bytes(TRANSACTION_TYPE.TRANSACTION_PAYMENT, length=2, byteorder='big')

        tx += int.to_bytes(STI_FIELDS.STI_UINT32 << 4 | FIELDS_IDS.XRP_UINT32_FLAGS, length=1, byteorder='big')
        tx += int.to_bytes(TF_FULLY_CANONICAL_SIG, length=4, byteorder='big') # sequence number

        tx += int.to_bytes(STI_FIELDS.STI_UINT32 << 4 | FIELDS_IDS.XRP_UINT32_SEQUENCE, length=1, byteorder='big')
        tx += int.to_bytes(1234, length=4, byteorder='big') # sequence number

        tx += int.to_bytes(STI_FIELDS.STI_UINT32 << 4 | FIELDS_IDS.XRP_VL_MEMO_FORMAT, length=1, byteorder='big')
        tx += int.to_bytes(int(memo), length=4, byteorder='big')

        tx += int.to_bytes(STI_FIELDS.STI_AMOUNT << 4 | FIELDS_IDS.XRP_UINT64_AMOUNT, length=1, byteorder='big')
        tx += int.to_bytes(0x4000000000000000 | send_amount, length=8, byteorder='big')

        tx += int.to_bytes(STI_FIELDS.STI_AMOUNT << 4 | FIELDS_IDS.XRP_UINT64_FEE, length=1, byteorder='big')
        tx += int.to_bytes(0x4000000000000000 | fees, length=8, byteorder='big')

        tx += int.to_bytes(STI_FIELDS.STI_VL << 4 | FIELDS_IDS.XRP_VL_SIGNING_PUB_KEY, length=1, byteorder='big')
        tx += int.to_bytes(XRP_PUBKEY_SIZE, length=1, byteorder='big')
        tx += addresscodec.decode_account_public_key("aBPM4Dk4bxMFEEBx93yU8DF2FSoUt19SDNPcGRsdzr6h9vhhPAGe")

        tx += int.to_bytes(STI_FIELDS.STI_ACCOUNT << 4 | FIELDS_IDS.XRP_ACCOUNT_ACCOUNT, length=1, byteorder='big')
        tx += int.to_bytes(XRP_ACCOUNT_SIZE, length=1, byteorder='big')
        tx += addresscodec.decode_classic_address("rTooLkitCksh5mQa67eaa2JaY7gzNePtD")

        tx += int.to_bytes(STI_FIELDS.STI_ACCOUNT << 4 | FIELDS_IDS.XRP_ACCOUNT_DESTINATION, length=1, byteorder='big')
        tx += int.to_bytes(XRP_ACCOUNT_SIZE, length=1, byteorder='big')
        tx += addresscodec.decode_classic_address(destination)

        return tx

    def send_simple_sign_tx(self, path: str, fees: int, memo: str, destination: str, send_amount: int) -> RAPDU:
        packed_path = pack_derivation_path(path)
        tx = self._craft_simple_tx(fees=fees, memo=memo, destination=destination, send_amount=send_amount)
        return self._backend.exchange(self.CLA, Ins.SIGN, P1.FIRST, P2.CURVE_SECP256K1, packed_path + tx)
