from enum import IntEnum

from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config, RAPDU

from secp256k1 import PublicKey

KAS_PATH = "m/44'/111111'/0'/0/0"
KAS_CONF = create_currency_config("KAS", "Kaspa")
KAS_PACKED_DERIVATION_PATH = pack_derivation_path(KAS_PATH)

# Check if a signature of a given message is valid
def check_signature_validity(public_key: bytes, signature: bytes, sighash: bytes) -> bool:
    pkey = PublicKey(public_key, True)
    
    return pkey.schnorr_verify(sighash, signature, None, True)
