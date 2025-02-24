import pytest
from pathlib import Path

from ragger.utils import RAPDU, prefix_with_len, create_currency_config
from ragger.error import ExceptionRAPDU

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors, Command, P2_EXTEND, P2_MORE, EXCHANGE_CLASS
from .apps.exchange_transaction_builder import get_partner_curve, LEGACY_SUBCOMMANDS, ALL_SUBCOMMANDS, NEW_SUBCOMMANDS, get_credentials, craft_and_sign_tx
from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps import cal as cal

ROOT_SCREENSHOT_PATH = Path(__file__).parent.resolve()

class TestDirect:

    def test_direct(self, backend, scenario_navigator):
        ex = ExchangeClient(backend)

        with pytest.raises(ExceptionRAPDU) as e:
            ex.direct_check_address("notanaddress", cal.ETH_CURRENCY_CONFIGURATION.get_conf_for_ticker())
        assert e.value.status == Errors.INVALID_ADDRESS

        ex.direct_check_address("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D", cal.ETH_CURRENCY_CONFIGURATION.get_conf_for_ticker())

        with ex.direct_format_amount(1000, cal.ETH_CURRENCY_CONFIGURATION.get_conf_for_ticker()):
            scenario_navigator.review_approve(path=ROOT_SCREENSHOT_PATH)
