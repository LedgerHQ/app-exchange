from ragger.utils import create_currency_config
from ragger.bip import pack_derivation_path

ETH_PATH = "m/44'/60'/0'/0/0"

ETH_CONF = create_currency_config("ETH", "Ethereum", ("ETH", 18))
ETH_PACKED_DERIVATION_PATH = pack_derivation_path(ETH_PATH)


# BSC_CONF = create_currency_config("BNB", "Binance Smart Chain", ("BNB", 18))
# BSC_PACKED_DERIVATION_PATH = pack_derivation_path(ETH_PATH)

BSC_CONF = create_currency_config("BNB", "Ethereum", ("BNB", 18))
BSC_PACKED_DERIVATION_PATH = pack_derivation_path(ETH_PATH)

ETC_PATH = "m/44'/60'/0'/0/0"

ETC_CONF = create_currency_config("ETC", "Ethereum Classic", ("ETC", 18))
ETC_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/61'/0'/0/0")
