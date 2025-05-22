import pytest

from ragger.utils import RAPDU, prefix_with_len, create_currency_config
from ragger.error import ExceptionRAPDU

from .ledger_app_clients.exchange.client import ExchangeClient, Rate, SubCommand, Errors, Command, P2_EXTEND, P2_MORE, EXCHANGE_CLASS
from .ledger_app_clients.exchange.transaction_builder import get_partner_curve, LEGACY_SUBCOMMANDS, ALL_SUBCOMMANDS, NEW_SUBCOMMANDS, get_credentials, craft_and_sign_tx
from .ledger_app_clients.exchange.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps import cal as cal
from .apps.ethereum import ETC_PACKED_DERIVATION_PATH

# This does not exist
CURRENCY_TO = cal.CurrencyConfiguration(ticker="PSM",
                                          conf=create_currency_config("PSM", "PSM"),
                                          packed_derivation_path=ETC_PACKED_DERIVATION_PATH)
CURRENCY_FROM = cal.ETH_CURRENCY_CONFIGURATION

# Some valid infos for TX. Content is irrelevant for the test

SWAP_TX_INFOS = {
     "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
     "payin_extra_id": b"",
     "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
     "refund_extra_id": b"",
     "payout_address": b"bc1qqtl9jlrwcr3fsfcjj2du7pu6fcgaxl5dsw2vyg",
     "payout_extra_id": b"",
     "currency_from": CURRENCY_FROM.ticker,
     "currency_to": CURRENCY_TO.ticker,
     "amount_to_provider": bytes.fromhex("013fc3a717fb5000"),
     "amount_to_wallet": b"\x0b\xeb\xc2\x00",
}
FEES = 100

@pytest.mark.use_on_backend("ledgerwallet")
def test_missing_application(backend):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP_NG)
    partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP_NG), name="Name")
    transaction_id = ex.init_transaction().data
    credentials = get_credentials(SubCommand.SWAP_NG, partner)
    ex.set_partner_key(credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
    tx, tx_signature = craft_and_sign_tx(SubCommand.SWAP_NG, SWAP_TX_INFOS, transaction_id, FEES, partner)
    ex.process_transaction(tx)
    ex.check_transaction_signature(tx_signature)
    to_configuration = CURRENCY_TO.get_conf_for_ticker()
    with pytest.raises(ExceptionRAPDU) as e:
        ex.check_payout_address(to_configuration)
    assert e.value.status == Errors.APPLICATION_NOT_INSTALLED
