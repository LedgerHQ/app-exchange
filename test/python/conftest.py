from pathlib import Path

from ragger.conftest import configuration


# Change this value to the name of your application
configuration.REQUIRED_CONFIGURATION["APP_NAME"] = "exchange"

# Change this path to the path in which your compiled elf files are located
configuration.REQUIRED_CONFIGURATION["APPS_DIRECTORY"] = (Path(__file__).parent.parent / "elfs").resolve()

configuration.OPTIONNAL_CONFIGURATION["SIDELOADED_APPS"] = {
    "bitcoin": "Bitcoin",
    "bitcoin_legacy": "Bitcoin Legacy",
    "ethereum": "Ethereum",
    "ethereum_classic": "Ethereum Classic",
    "tezos": "Tezos Wallet",
    "xrp": "RXP",
    "litecoin": "Litecoin",
    "stellar": "Stellar",
    "solana": "Solana",
}

configuration.OPTIONAL_CONFIGURATION["BACKEND_SCOPE"] = "function"


# Pull all features from the base ragger conftest using the overridden configuration
from ragger.conftest.base_conftest import *
