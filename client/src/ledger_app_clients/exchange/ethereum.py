# All swap tests are performed against ETH so we shall define the ETH configuration here.
from typing import Optional
import struct
from ragger.bip import pack_derivation_path


def get_sub_config(swapped_asset_ticker: str,
                   swapped_asset_decimals: int,
                   chain_id: int,
                   fees_asset_ticker: Optional[str] = None,
                   fees_asset_decimals: Optional[int] = None) -> bytes:
    cfg = bytearray()
    # Append asset ticker length and ticker
    cfg.append(len(swapped_asset_ticker))
    cfg += swapped_asset_ticker.encode()
    # Append asset decimals
    cfg.append(swapped_asset_decimals)
    # Append chain id
    cfg += struct.pack(">Q", chain_id)
    # TODO: To remove when CAL is updated and always send the native ticker and decimals
    if fees_asset_ticker is not None:
        # Append network ticker length and ticker if any
        cfg.append(len(fees_asset_ticker))
        cfg += fees_asset_ticker.encode()
        if fees_asset_decimals is not None:
            # Append network asset decimals if any
            cfg.append(fees_asset_decimals)
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
ETH_CONF = create_currency_config("ETH", "Ethereum", get_sub_config("ETH", 18, 1, "ETH", 18))
ETH_PACKED_DERIVATION_PATH = pack_derivation_path(ETH_PATH)

