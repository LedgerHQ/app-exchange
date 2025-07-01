from ragger.utils import create_currency_config
from ragger.bip import pack_derivation_path
from bip_utils import Bip32Utils
from nacl.signing import VerifyKey

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

USDC_AMOUNT       = 100023 #0.100023 USDC
USDC_AMOUNT_2     = 123393 #0.123393 USDC

# Balances of objects used in these tests
USDC_OBJECTS_BY_AMOUNT = {
    # 0xd3baa97a46a20d65f1be60cbaa160856e6aae5078e16545071e2fd3e314105b9 USDC  100023 (0.100023 USDC)
    100023: {
        'obj': 'AAMH26NGcuMMsGWx+T46tVMYdo/W/vZsFZQsn3y4RuL5AOcEdXNkYwRVU0RDAAF2L6QdAAAAACjTuql6RqINZfG+YMuqFghW5qrlB44WVFBx4v0+MUEFubeGAQAAAAAAAA8vjdSeJp2gZvN2JNM6i07RsmLWpf3ytzW+OfjXxaz1ICV9oiz28QN2+VFgs3VVcob35zoaZgQf5WcAe9gWdNyWoC0UAAAAAAA=',
        'object_id': '0xd3baa97a46a20d65f1be60cbaa160856e6aae5078e16545071e2fd3e314105b9',
        'version': 497299318,
        'digest': 'BWyUBdTBr7uMyQ1nRsQkkB5RXLNL6QWprGaqJ7atMJTC'
    },
    # 0x8ba6495be346c1be89e5c35cdabab145ea18990f48f2b0629ff016024c9ded45 USDC  123393 (0.123393 USDC)
    123393: {
        'obj': 'AAMH26NGcuMMsGWx+T46tVMYdo/W/vZsFZQsn3y4RuL5AOcEdXNkYwRVU0RDAAE1MqYdAAAAACiLpklb40bBvonlw1zaurFF6hiZD0jysGKf8BYCTJ3tRQHiAQAAAAAAAA8vjdSeJp2gZvN2JNM6i07RsmLWpf3ytzW+OfjXxaz1IOV7R/YfpK7xICsKift4S9G6tE2+t4MyPAX4gSGmkRIYoC0UAAAAAAA=',
        'object_id': '0x8ba6495be346c1be89e5c35cdabab145ea18990f48f2b0629ff016024c9ded45',
        'version': 497431093,
        'digest': '5DEmU82eeP1wJ6L7q8V7bLbAr4Vbjat2XkT3nbf5NmSN'
    }
}

FEES            = sui_to_mist(0.00000564)
FEES_BYTES      = mist_to_bytes(FEES)

FEES_2            = sui_to_mist(0.0005543)
FEES_2_BYTES      = mist_to_bytes(FEES_2)


### Proposed foreign and owned addresses ###

# "Foreign" Sui public key (actually the device public key derived on m/44'/784'/11111')
FOREIGN_ADDRESS      = "0x5a64eec558ee719741578942714a0b35058ced15d79f4af64da014715ada4497"
FOREIGN_PUBLIC_KEY   = "4857ad1ffa9dbca7f5cab2187455cece1ae3367975f71087019ba9642d64555b"

# "Foreign" Sui public key (actually the device public key derived on m/44'/784'/11112')
FOREIGN_ADDRESS_2    = "0x87aa2830134adc42ed726fde1755e2af38469920314f936755de616c3b4b46fd"
FOREIGN_PUBLIC_KEY_2 = "ea7d26fe9f91d35dfaeca579b0c94445e3902fc63fd997107a21a39886613b2c"

# Device Sui public key (derived on m/44'/784'/12345')
OWNED_ADDRESS        = "0xd5a6dc2129672c36d318ecc28c96a25fdf640933d6ed8840b1f78171f50f9cc9"
OWNED_PUBLIC_KEY     = "5abb58c686211fa0dcbcb6455e80ae8af2ec52483d4761b95d025ce935f9cff4"

def verify_signature(from_public_key: bytes, message: bytes, signature: bytes):
    assert len(signature) == 64, "signature size incorrect"
    verify_key = VerifyKey(from_public_key)
    verify_key.verify(message, signature)

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

# Used in app-sui commands (litte endian byte order)
SUI_PACKED_DERIVATION_PATH_LE = sui_pack_derivation_path("m/44'/784'/12345'")
# Used in swap params (standard big endian byte order)
SUI_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/784'/12345'")

### Package this currency configuration in exchange format ###

SUI_CONF = create_currency_config("SUI", "Sui")
SUI_USDC_CONF = create_currency_config("USDC", "Sui", ("USDC", 6))
