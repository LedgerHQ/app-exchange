import sys
import base64
from pathlib import Path
from fastcrc import crc16
from enum import IntEnum

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config
from ragger.error import ExceptionRAPDU

TON_CONF = create_currency_config("TON", "TON")

TON_DERIVATION_PATH = "m/44'/607'/0'/0'/0'/0'"
TON_PACKED_DERIVATION_PATH = pack_derivation_path(TON_DERIVATION_PATH)
DEVICE_PUBLIC_KEY = bytes.fromhex("9aff66dcc01b79787f6038c8070b8f7b9f27e381297c846a59f743bb075ed61c")

SW_SWAP_FAILURE = 0xB009

MAX_APDU_LEN: int = 255
CLA = 0xE0

class Bounceability(IntEnum):
    BOUNCEABLE = 0x11
    NON_BOUNCEABLE = 0x51

class WorkchainID(IntEnum):
    BASE_CHAIN = 0x00
    MASTER_CHAIN = 0xff

def craft_address(bounceability: Bounceability, workchain_id: WorkchainID, device_public_key: bytes):
    payload = b''
    payload += int.to_bytes(bounceability, length=1, byteorder='big')
    payload += int.to_bytes(workchain_id, length=1, byteorder='big')
    payload += device_public_key
    payload += int.to_bytes(crc16.xmodem(payload), length=2, byteorder='big')
    return base64.b64encode(payload)
