from enum import IntEnum

from ragger.backend.interface import BackendInterface, RAPDU
from .ethereum import create_currency_config
from ragger.bip import pack_derivation_path

def get_sub_config(ticker: str, decimals: int) -> bytes:
    cfg = bytearray()
    cfg.append(len(ticker))
    cfg += ticker.encode()
    cfg.append(decimals)
    return cfg

class Errors(IntEnum):
    SW_SWAP_CHECKING_FAIL      = 0xB00A

CELO_CONF = create_currency_config("CELO", "Celo", get_sub_config("CELO", 18))
CELO_PATH = "m/44'/52752'/0'/0/0"
CELO_PACKED_DERIVATION_PATH = pack_derivation_path(CELO_PATH)
