from pathlib import Path

from ragger.conftest import configuration


configuration.OPTIONAL_CONFIGURATION["SIDELOADED_APPS"] = {
    "bitcoin": "Bitcoin",
    "bitcoin_legacy": "Bitcoin Legacy",
    "ethereum": "Ethereum",
    "ethereum_classic": "Ethereum Classic",
    "tezos": "Tezos Wallet",
    "xrp": "RXP",
    "litecoin": "Litecoin",
    "stellar": "Stellar",
}

configuration.OPTIONAL_CONFIGURATION["SIDELOADED_APPS_DIR"] = "test/libs"

configuration.OPTIONAL_CONFIGURATION["BACKEND_SCOPE"] = "function"


# Pull all features from the base ragger conftest using the overridden configuration
from ragger.conftest.base_conftest import *
