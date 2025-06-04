# All swap tests are performed against ETH so we shall define the ETH configuration here.
from typing import Optional
import struct
from ragger.bip import pack_derivation_path


def get_sub_config(ticker: str, decimals: int, chain_id: Optional[int] = None) -> bytes:
    cfg = bytearray()
    cfg.append(len(ticker))
    cfg += ticker.encode()
    cfg.append(decimals)
    if chain_id is not None:
        cfg += struct.pack(">Q", chain_id)
    return cfg


def create_currency_config(main_ticker: str,
                           application_name: str,
                           sub_config: bytes = bytes()) -> bytes:
    cfg = bytearray()
    for elem in [main_ticker.encode(), application_name.encode(), sub_config]:
        cfg.append(len(elem))
        cfg += elem
    return cfg


ETH_PATH = "m/44'/60'/0'/0/0"
ETH_CONF = create_currency_config("ETH", "Ethereum", get_sub_config("ETH", 18))
ETH_PACKED_DERIVATION_PATH = pack_derivation_path(ETH_PATH)

