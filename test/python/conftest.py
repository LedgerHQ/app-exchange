import pytest

from ragger.conftest import configuration

from .apps.exchange_navigation_helper import ExchangeNavigationHelper

###########################
### CONFIGURATION START ###
###########################

# You can configure optional parameters by overriding the value of ragger.configuration.OPTIONAL_CONFIGURATION
# Please refer to ragger/conftest/configuration.py for their descriptions and accepted values

configuration.OPTIONAL.APP_NAME = "Exchange"

configuration.OPTIONAL.SIDELOADED_APPS = {
    "bitcoin": "Bitcoin",
    "bitcoin_legacy": "Bitcoin Legacy",
    "ethereum": "Ethereum",
    "ethereum_classic": "Ethereum Classic",
    "tezos": "Tezos Wallet",
    "xrp": "XRP",
    "litecoin": "Litecoin",
    "stellar": "Stellar",
    "solana": "Solana",
    "bsc": "Binance Smart Chain",
}

configuration.OPTIONAL.SIDELOADED_APPS_DIR = "test/python/lib_binaries/"

configuration.OPTIONAL.BACKEND_SCOPE = "function"

#########################
### CONFIGURATION END ###
#########################

# Pull all features from the base ragger conftest using the overridden configuration
pytest_plugins = ("ragger.conftest.base_conftest", )

@pytest.fixture(scope="function")
def exchange_navigation_helper(backend, navigator, test_name):
    return ExchangeNavigationHelper(backend=backend, navigator=navigator, test_name=test_name)
