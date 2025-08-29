import pytest

from ragger.utils import RAPDU, prefix_with_len, create_currency_config
from ragger.error import ExceptionRAPDU

from ledger_app_clients.exchange.client import ExchangeClient, Rate, SubCommand, Errors, Command, P2_EXTEND, P2_MORE, EXCHANGE_CLASS
from ledger_app_clients.exchange.transaction_builder import get_partner_curve, LEGACY_SUBCOMMANDS, ALL_SUBCOMMANDS, NEW_SUBCOMMANDS, get_credentials, craft_and_sign_tx
from ledger_app_clients.exchange.signing_authority import SigningAuthority, LEDGER_SIGNER
from ledger_app_clients.exchange.utils import handle_lib_call_start_or_stop
from .apps import cal as cal
from .apps.ethereum import ETC_PACKED_DERIVATION_PATH, ETH_PATH
from ledger_app_clients.ethereum.client import EthAppClient

CURRENCY_FROM = cal.ETH_CURRENCY_CONFIGURATION
CURRENCY_TO = cal.ETH_CURRENCY_CONFIGURATION

# Some valid infos for TX. Content is irrelevant for the test

SWAP_TX_INFOS = {
     "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
     "payin_extra_id": b"",
     "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
     "refund_extra_id": b"",
     "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
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
    SubCommand.SWAP_NG: SWAP_TX_INFOS,
    SubCommand.FUND_NG: FUND_TX_INFOS,
    SubCommand.SELL_NG: SELL_TX_INFOS,
}
FEES = 100

class TestRejection:
    def _prepare_swap(self, ex, exchange_navigation_helper, subcommand, fake_payout_address=None):
        # Add a "_fund" / "_sell" / "_swap" suffix to the snapshot directory
        suffix = "_" + subcommand.get_operation
        exchange_navigation_helper.set_test_name_suffix(suffix)

        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx_infos = TX_INFOS[subcommand].copy()
        if fake_payout_address is not None:
            tx_infos["payout_address"] = fake_payout_address
        tx, tx_signature = craft_and_sign_tx(subcommand, tx_infos, transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        if subcommand == SubCommand.SWAP_NG:
            to_configuration = CURRENCY_TO.get_conf_for_ticker()
            ex.check_payout_address(to_configuration)

        from_configuration = CURRENCY_FROM.get_conf_for_ticker()
        if subcommand == SubCommand.SWAP_NG:
            ex.check_refund_address_no_display(from_configuration)
        else:
            ex.check_asset_in_no_display(from_configuration)

    @pytest.mark.parametrize("subcommand", NEW_SUBCOMMANDS)
    def test_rejection(self, backend, exchange_navigation_helper, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        self._prepare_swap(ex, exchange_navigation_helper, subcommand)

        # Request the final address check and UI approval request on the device
        with pytest.raises(ExceptionRAPDU) as e:
            with ex.prompt_ui_display():
                exchange_navigation_helper.simple_reject()
        assert e.value.status == Errors.USER_REFUSED_TRANSACTION

        # Ensure Exchange refuses to start the libary application
        # We should have reset the internal context and be ready for a new TX proposal
        with pytest.raises(ExceptionRAPDU) as e:
            ex.start_signing_transaction()
        assert e.value.status == Errors.UNEXPECTED_INSTRUCTION

    def test_cross_seed_rejection(self, backend, exchange_navigation_helper):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP_NG)
        self._prepare_swap(ex, exchange_navigation_helper, SubCommand.SWAP_NG, fake_payout_address=b'bc1qqtl9jlrwcr3fsfcjj2du7pu6fcgaxl5dsw2vyg0000')

        # Request the final address check and UI approval request on the device
        with pytest.raises(ExceptionRAPDU) as e:
            with ex.prompt_ui_display():
                exchange_navigation_helper.cross_seed_reject()
        assert e.value.status == Errors.USER_REFUSED_CROSS_SEED

        # Ensure Exchange refuses to start the libary application
        # We should have reset the internal context and be ready for a new TX proposal
        with pytest.raises(ExceptionRAPDU) as e:
            ex.start_signing_transaction()
        assert e.value.status == Errors.UNEXPECTED_INSTRUCTION

    def test_cross_seed_accept_then_reject(self, backend, exchange_navigation_helper):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP_NG)
        self._prepare_swap(ex, exchange_navigation_helper, SubCommand.SWAP_NG, fake_payout_address=b'bc1qqtl9jlrwcr3fsfcjj2du7pu6fcgaxl5dsw2vyg0000')

        # Request the final address check and UI approval request on the device
        with pytest.raises(ExceptionRAPDU) as e:
            with ex.prompt_ui_display():
                exchange_navigation_helper.cross_seed_accept()
                exchange_navigation_helper.simple_reject()
        assert e.value.status == Errors.USER_REFUSED_TRANSACTION

        # Ensure Exchange refuses to start the libary application
        # We should have reset the internal context and be ready for a new TX proposal
        with pytest.raises(ExceptionRAPDU) as e:
            ex.start_signing_transaction()
        assert e.value.status == Errors.UNEXPECTED_INSTRUCTION

    def _cross_swap_valid(self, backend, exchange_navigation_helper, payout_address, fixed_rate=True):
        rate = Rate.FIXED if fixed_rate else Rate.FLOATING
        ex = ExchangeClient(backend, rate, SubCommand.SWAP_NG)
        self._prepare_swap(ex, exchange_navigation_helper, SubCommand.SWAP_NG, fake_payout_address=payout_address)

        # Request the final address check and UI approval request on the device
        with ex.prompt_ui_display():
            exchange_navigation_helper.cross_seed_accept()
            exchange_navigation_helper.simple_accept()

        exchange_navigation_helper.wait_for_exchange_spinner()
        ex.start_signing_transaction()
        handle_lib_call_start_or_stop(backend)
        exchange_navigation_helper.wait_for_library_spinner()

        app_client = EthAppClient(backend)
        with app_client.sign(bip32_path=ETH_PATH,
                             tx_params={
                                 "nonce": 0,
                                 "gasPrice": 1,
                                 "gas": FEES,
                                 "to": "0xd692Cb1346262F584D17B4B470954501f6715a82",
                                 "value": 0x013fc3a717fb5000,
                                 "chainId": 1,
                             }):
            pass

        exchange_navigation_helper.check_post_sign_display()
        handle_lib_call_start_or_stop(backend)
        ex.assert_exchange_is_started()

    def test_cross_seed_accept_then_accept_short_length(self, backend, exchange_navigation_helper):
        self._cross_swap_valid(backend, exchange_navigation_helper, b'0')

    def test_cross_seed_accept_then_accept_medium_length(self, backend, exchange_navigation_helper):
        self._cross_swap_valid(backend, exchange_navigation_helper, b'0xd692Cb1346262F584D17B4B470954501f6715a82')

    def test_cross_seed_accept_then_accept_max_length(self, backend, exchange_navigation_helper):
        self._cross_swap_valid(backend, exchange_navigation_helper, b'bc1qqtl9jlrwcr3fsfcjj2du7pu6fcgaxl5dsw2vyg0000bc1qqtl9jlrwcr3fsfcjj2du7pu6fcgaxl5dsw2vyg0000bc1qqtl9jlrwcr3fsfcjj2du7pu6fcgaxl5dsw2vyg0000bc1qqtl9jlrw')

    def test_cross_seed_accept_then_accept_floating(self, backend, exchange_navigation_helper):
        self._cross_swap_valid(backend, exchange_navigation_helper, b'0xd692Cb1346262F584D17B4B470954501f6715a82', fixed_rate=False)
