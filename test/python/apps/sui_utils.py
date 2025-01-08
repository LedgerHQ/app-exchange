import base58

from ragger.utils import create_currency_config
from bip_utils import Bip32Utils
from ragger.bip import pack_derivation_path

### Some utilities functions for amounts conversions ###

def sui_to_mist(sui_amount: int) -> int:
    return round(sui_amount * 10**9)


def mist_to_bytes(mists: int) -> str:
    hex:str = '{:x}'.format(mists)
    if (len(hex) % 2 != 0):
        hex = "0" + hex
    return bytes.fromhex(hex)


### Proposed values for fees and amounts ###

AMOUNT          = sui_to_mist(2.078)
AMOUNT_BYTES    = mist_to_bytes(AMOUNT)

AMOUNT_2        = sui_to_mist(101.000001234)
AMOUNT_2_BYTES  = mist_to_bytes(AMOUNT_2)

FEES            = sui_to_mist(0.00000564)
FEES_BYTES      = mist_to_bytes(FEES)

FEES_2            = sui_to_mist(0.0005543)
FEES_2_BYTES      = mist_to_bytes(FEES_2)


### Proposed foreign and owned addresses ###

# "Foreign" Sui public key (actually the device public key derived on m/44'/784'/11111')
FOREIGN_ADDRESS      = b"0x5a64eec558ee719741578942714a0b35058ced15d79f4af64da014715ada4497"
FOREIGN_PUBLIC_KEY   = FOREIGN_ADDRESS

# "Foreign" Sui public key (actually the device public key derived on m/44'/784'/11112')
FOREIGN_ADDRESS_2    = b"0x87aa2830134adc42ed726fde1755e2af38469920314f936755de616c3b4b46fd"
FOREIGN_PUBLIC_KEY_2 = FOREIGN_ADDRESS_2

# Device Sui public key (derived on m/44'/501'/12345')
OWNED_ADDRESS        = b"0xd5a6dc2129672c36d318ecc28c96a25fdf640933d6ed8840b1f78171f50f9cc9"
OWNED_PUBLIC_KEY     = OWNED_ADDRESS


### Proposed Sui derivation paths for tests ###

# For some reason SUI coin app expects path in little endian byte order
def sui_pack_derivation_path(derivation_path: str) -> bytes:
    split = derivation_path.split("/")

    if split[0] != "m":
        raise ValueError("Error master expected")

    path_bytes: bytes = (len(split) - 1).to_bytes(1, byteorder='little')
    for value in split[1:]:
        if value == "":
            raise ValueError(f'Error missing value in split list "{split}"')
        if value.endswith('\''):
            path_bytes += Bip32Utils.HardenIndex(int(value[:-1])).to_bytes(4, byteorder='little')
        else:
            path_bytes += int(value).to_bytes(4, byteorder='little')
    return path_bytes

SUI_PACKED_DERIVATION_PATH = sui_pack_derivation_path("m/44'/784'/12345'")

### Package this currency configuration in exchange format ###

SUI_CONF = create_currency_config("SUI", "Sui")
