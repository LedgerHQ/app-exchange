import base58

from ragger.utils import create_currency_config
from ragger.bip import pack_derivation_path
from typing import Optional
import struct

### Some utilities functions for amounts conversions ###

def sol_to_lamports(sol_amount: int) -> int:
    return round(sol_amount * 10**9)


def lamports_to_bytes(lamports: int) -> str:
    hex:str = '{:x}'.format(lamports)
    if (len(hex) % 2 != 0):
        hex = "0" + hex
    return bytes.fromhex(hex)


### Proposed values for fees and amounts ###

AMOUNT          = sol_to_lamports(2.078)
AMOUNT_BYTES    = lamports_to_bytes(AMOUNT)

AMOUNT_2        = sol_to_lamports(101.000001234)
AMOUNT_2_BYTES  = lamports_to_bytes(AMOUNT_2)

FEES            = sol_to_lamports(0.00000564)
FEES_BYTES      = lamports_to_bytes(FEES)

FEES_2            = sol_to_lamports(0.0005543)
FEES_2_BYTES      = lamports_to_bytes(FEES_2)


### Proposed foreign and owned addresses ###

# "Foreign" Solana public key (actually the device public key derived on m/44'/501'/11111')
FOREIGN_ADDRESS_STR = "AxmUF3qkdz1zs151Q5WttVMkFpFGQPwghZs4d1mwY55d"
FOREIGN_ADDRESS     = FOREIGN_ADDRESS_STR.encode('utf-8')
FOREIGN_PUBLIC_KEY  = base58.b58decode(FOREIGN_ADDRESS)

# "Foreign" Solana public key (actually the device public key derived on m/44'/501'/11112')
FOREIGN_ADDRESS_2_STR   = "8bjDMujLMttbmkTtoFgfw2sPYchSzzcTCEPGYDaNs3nj"
FOREIGN_ADDRESS_2       = FOREIGN_ADDRESS_2_STR.encode('utf-8')
FOREIGN_PUBLIC_KEY_2    = base58.b58decode(FOREIGN_ADDRESS_2)

# Device Solana public key (derived on m/44'/501'/12345')
OWNED_ADDRESS_STR   = "3GJzvStsiYZonWE7WTsmt1BpWXkfcgWMGinaDwNs9HBc"
OWNED_ADDRESS       = OWNED_ADDRESS_STR.encode('utf-8')
OWNED_PUBLIC_KEY    = base58.b58decode(OWNED_ADDRESS)


### Proposed Solana derivation paths for tests ###

SOL_PACKED_DERIVATION_PATH      = pack_derivation_path("m/44'/501'/12345'")
SOL_PACKED_DERIVATION_PATH_2    = pack_derivation_path("m/44'/501'/0'/0'")


### Package this currency configuration in exchange format ###

SOL_CONF = create_currency_config("SOL", "Solana")

def get_sub_config(ticker: str, decimals: int, chain_id: Optional[int] = None) -> bytes:
    cfg = bytearray()
    cfg.append(len(ticker))
    cfg += ticker.encode()
    cfg.append(decimals)
    if chain_id is not None:
        cfg += struct.pack(">Q", chain_id)
    return cfg

JUP_CONF = create_currency_config("JUP", "Solana", get_sub_config("JUP", 6))
JUP_PACKED_DERIVATION_PATH = SOL_PACKED_DERIVATION_PATH

JUP_MINT_ADDRESS_STR = "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"