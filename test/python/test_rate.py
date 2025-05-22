import pytest

from ragger.utils import RAPDU, prefix_with_len, create_currency_config
from ragger.error import ExceptionRAPDU

from ledger_app_clients.exchange.client import ExchangeClient, Rate, SubCommand, Errors, Command, P2_EXTEND, P2_MORE, EXCHANGE_CLASS
from ledger_app_clients.exchange.transaction_builder import get_partner_curve, LEGACY_SUBCOMMANDS, ALL_SUBCOMMANDS, NEW_SUBCOMMANDS, get_credentials, craft_and_sign_tx
from ledger_app_clients.exchange.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps import cal as cal

CURRENCY_FROM = cal.ETH_CURRENCY_CONFIGURATION
CURRENCY_TO = cal.BTC_CURRENCY_CONFIGURATION

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
FUND_TX_INFOS = {
    "user_id": "John Wick",
    "account_name": "Remember Daisy",
    "in_currency": CURRENCY_FROM.ticker,
    "in_amount": b"\032\200\250]$T\000",
    "in_address": "0x252fb4acbe0de4f0bd2409a5ed59a71e4ef1d2bc"
}
SELL_TX_INFOS = {
    "trader_email": "john@doe.lost",
    "out_currency": "USD",
    "out_amount": {"coefficient": b"\x01", "exponent": 3},
    "in_currency": CURRENCY_FROM.ticker,
    "in_amount": b"\032\200\250]$T\000",
    "in_address": "0x252fb4acbe0de4f0bd2409a5ed59a71e4ef1d2bc"
}
TX_INFOS = {
    SubCommand.SWAP: SWAP_TX_INFOS,
    SubCommand.SWAP_NG: SWAP_TX_INFOS,
    SubCommand.FUND: FUND_TX_INFOS,
    SubCommand.FUND_NG: FUND_TX_INFOS,
    SubCommand.SELL: SELL_TX_INFOS,
    SubCommand.SELL_NG: SELL_TX_INFOS,
}
FEES = 100

class TestRate:

    @pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
    def test_rate(self, backend, subcommand, exchange_navigation_helper):
        # Mutualize new and legacy snapshots. Eg SubCommand.SWAP_NG => "swap"
        suffix = "_" + str(subcommand).split('.')[1].split('_')[0].lower()
        exchange_navigation_helper.set_test_name_suffix(suffix)

        # Test only FLOATING, all other tests are using FIXED
        ex = ExchangeClient(backend, Rate.FLOATING, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")

        transaction_id = ex.init_transaction().data

        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))

        tx_infos = TX_INFOS[subcommand]
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        ex.process_transaction(tx)

        ex.check_transaction_signature(tx_signature)

        if subcommand == SubCommand.SWAP or subcommand == SubCommand.SWAP_NG:
            ex.check_payout_address(CURRENCY_TO.get_conf_for_ticker())

            with ex.check_refund_address(CURRENCY_FROM.get_conf_for_ticker()):
                exchange_navigation_helper.simple_accept()
        else:
            with ex.check_asset_in(CURRENCY_FROM.get_conf_for_ticker()):
                exchange_navigation_helper.simple_accept()
