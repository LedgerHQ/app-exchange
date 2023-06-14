from ragger.utils import create_currency_config
from ragger.bip import pack_derivation_path

ETC_CONF = create_currency_config("ETC", "Ethereum Classic", ("ETC", 18))

ETC_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/61'/0'/0/0")
