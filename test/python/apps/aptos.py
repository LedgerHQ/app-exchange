from ragger.utils import create_currency_config
from ragger.bip import pack_derivation_path

APTOS_CONF = create_currency_config("APT", "Aptos")
APTOS_DERIVATION_PATH = "m/44'/637'/0'"
APTOS_PACKED_DERIVATION_PATH = pack_derivation_path(APTOS_DERIVATION_PATH)

MAX_APDU_LEN: int = 255