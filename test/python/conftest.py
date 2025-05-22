import pytest

from ragger.conftest import configuration

from .ledger_app_clients.exchange.navigation_helper import ExchangeNavigationHelper

###########################
### CONFIGURATION START ###
###########################

# You can configure optional parameters by overriding the value of ragger.configuration.OPTIONAL_CONFIGURATION
# Please refer to ragger/conftest/configuration.py for their descriptions and accepted values

configuration.OPTIONAL.ALLOWED_SETUPS = ["default", "prod_build"]
configuration.OPTIONAL.BACKEND_SCOPE = "class"

# --8<-- [start:sideloaded_applications]
def pytest_configure(config):
    current_setup = config.getoption("--setup")
    # We don't need any lib dependency for the prod_build test
    if current_setup == "default":
        # List of sideloaded applications under the format <VARIANT_VALUES>:<APPNAME>
        configuration.OPTIONAL.SIDELOADED_APPS = {
            "APTOS": "Aptos",
            "bitcoin": "Bitcoin",
            "bitcoin_legacy": "Bitcoin Legacy",
            "ethereum": "Ethereum",
            "ethereum_classic": "Ethereum Classic",
            "tezos": "Tezos Wallet",
            "xrp": "XRP",
            "litecoin": "Litecoin",
            "stellar": "Stellar",
            "solana": "Solana",
            "DOT": "Polkadot",
            "tron": "Tron",
            "ton": "TON",
            "ATOM": "Cosmos",
            "cardano": "Cardano ADA",
            "near": "NEAR",
            "sui": "Sui",
            "boilerplate": "Boilerplate"
        }

        configuration.OPTIONAL.SIDELOADED_APPS_DIR = "test/python/lib_binaries/"
# --8<-- [end:sideloaded_applications]


#########################
### CONFIGURATION END ###
#########################

# Pull all features from the base ragger conftest using the overridden configuration
pytest_plugins = ("ragger.conftest.base_conftest", )

@pytest.fixture(scope="function")
def exchange_navigation_helper(backend, navigator, test_name):
    return ExchangeNavigationHelper(backend=backend, navigator=navigator, test_name=test_name)

# Pytest is trying to do "smart" stuff and reorders tests using parametrize by alphabetical order of parameter
# This breaks the backend scope optim. We disable this
def pytest_collection_modifyitems(config, items):
    def param_part(item):
        # Sort by node id as usual
        return item.nodeid

    # re-order the items using the param_part function as key
    items[:] = sorted(items, key=param_part)
