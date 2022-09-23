from typing import Optional
from pathlib import Path
from bip32 import HARDENED_INDEX
from enum import IntEnum

from ragger.backend import SpeculosBackend

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


def app_path_from_app_name(app_dir, app_name: str, device: str) -> Path:
    assert app_dir.is_dir(), f"{app_dir} is not a directory"
    app_path = app_dir / (app_name + "_" + device + ".elf")
    assert app_path.is_file(), f"{app_path} must exist"
    return app_path

def concatenate(*args):
    result = b''
    for arg in args:
        result += (bytes([len(arg)]) + arg)
    return result

def validate_displayed_message(client: SpeculosBackend, num_screen_skip: int):
    for _ in range(num_screen_skip):
        client.right_click()
    client.both_click()

# DERIVATION PATHS CALCULATIONS

class BtcDerivationPathFormat(IntEnum):
    LEGACY      = 0x00
    P2SH        = 0x01
    BECH32      = 0x02
    CASHADDR    = 0x03 # Deprecated
    BECH32M     = 0x04

def pack_derivation_path(derivation_path: str) -> bytes:
    split = derivation_path.split("/")
    assert split.pop(0) == "m", "master expected"
    derivation_path: bytes = (len(split)).to_bytes(1, byteorder='big')
    for i in split:
        if (i[-1] == "'"):
            derivation_path += (int(i[:-1]) | HARDENED_INDEX).to_bytes(4, byteorder='big')
        else:
            derivation_path += int(i).to_bytes(4, byteorder='big')
    return derivation_path

def bitcoin_pack_derivation_path(format: BtcDerivationPathFormat, derivation_path: str) -> bytes:
    assert isinstance(format, BtcDerivationPathFormat)
    return format.to_bytes(1, "big") + pack_derivation_path(derivation_path)


# CURRENCY CONFIG CALCULATIONS

def create_sub_currency_config(ticker: str, number: int) -> bytes:
    sub_coin_config: buffer = b""
    sub_coin_config += (len(ticker)).to_bytes(1, byteorder='big')
    sub_coin_config += ticker.encode('utf-8')
    sub_coin_config += (number).to_bytes(1, byteorder='big')
    return sub_coin_config

def create_currency_config(ticker: str, application_name: str, sub_coin_config: bytes = b"") -> bytes:
    coin_config: buffer = b""
    coin_config += (len(ticker)).to_bytes(1, byteorder='big')
    coin_config += ticker.encode('utf-8')
    coin_config += (len(application_name)).to_bytes(1, byteorder='big')
    coin_config += application_name.encode('utf-8')
    coin_config += (len(sub_coin_config)).to_bytes(1, byteorder='big')
    coin_config += sub_coin_config
    return coin_config
