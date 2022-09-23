from ..utils import create_currency_config, create_sub_currency_config, pack_derivation_path

ETC_CONF = create_currency_config("ETC", "Ethereum Classic", create_sub_currency_config("ETC", 18))

ETC_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/61'/0'/0/0")
