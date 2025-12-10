from ragger.bip import pack_derivation_path

from ledger_app_clients.exchange.ethereum import get_sub_config, create_currency_config
from ledger_app_clients.exchange.ethereum import ETH_PATH

# Monad (MON) configuration
MON_CONF = create_currency_config("MON", "Ethereum", get_sub_config("MON", 18, 143, "MON", 18))
MON_PACKED_DERIVATION_PATH = pack_derivation_path(ETH_PATH)

# Use Ethereum app
BSC_CONF = create_currency_config("BNB", "Ethereum", get_sub_config("BNB", 18, 56, "BNB", 18))
BSC_PACKED_DERIVATION_PATH = pack_derivation_path(ETH_PATH)

ETC_PATH = "m/44'/61'/0'/0/0"
ETC_CONF = create_currency_config("ETC", "Ethereum Classic", get_sub_config("ETC", 18, 61, "ETC", 18))
ETC_PACKED_DERIVATION_PATH = pack_derivation_path(ETC_PATH)

# DAI configuration without native ticker and decimals to ensure retrocompatibility checks
DAI_CONF = create_currency_config("DAI", "Ethereum", get_sub_config("DAI", 18, 1))
DAI_PACKED_DERIVATION_PATH = pack_derivation_path(ETH_PATH)
