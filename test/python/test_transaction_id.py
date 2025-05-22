import pytest

from ragger.utils import RAPDU
from ragger.error import ExceptionRAPDU

from .ledger_app_clients.exchange.client import ExchangeClient, Rate, SubCommand, Errors
from .ledger_app_clients.exchange.transaction_builder import get_partner_curve, ALL_SUBCOMMANDS, get_credentials, craft_and_sign_tx
from .ledger_app_clients.exchange.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps import cal as cal

CURRENCY_FROM = cal.ETH_CURRENCY_CONFIGURATION
CURRENCY_TO = cal.BTC_CURRENCY_CONFIGURATION

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


class TestTransactionID:

    def test_transaction_id_format(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        transaction_id = ex.init_transaction().data
        # Assert length
        assert len(transaction_id) == 10
        # Assert that we only received upper char ascii characters
        decoded = transaction_id.decode(errors='ignore')
        assert decoded.encode('ascii', errors='ignore') == transaction_id
        assert decoded.isalpha()
        assert decoded.isupper()

        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SELL)
        transaction_id = ex.init_transaction().data
        # Assert length
        assert len(transaction_id) == 32

        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.FUND)
        transaction_id = ex.init_transaction().data
        # Assert length
        assert len(transaction_id) == 32

    @pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
    def test_wrong_transaction_id(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="partner")

        original_transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))

        transaction_id = original_transaction_id + b'0x0'
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        with pytest.raises(ExceptionRAPDU) as e:
            ex.process_transaction(tx)
        assert e.value.status == Errors.DESERIALIZATION_FAILED

        transaction_id = original_transaction_id[:-1]
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        with pytest.raises(ExceptionRAPDU) as e:
            ex.process_transaction(tx)
        assert e.value.status == Errors.WRONG_TRANSACTION_ID

        transaction_id_bytearray_version = bytearray(transaction_id)
        if transaction_id_bytearray_version[-1] == 255:
            transaction_id_bytearray_version[-1] = 0
        else:
            transaction_id_bytearray_version[-1] += 1
        transaction_id = bytes(transaction_id_bytearray_version)
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        with pytest.raises(ExceptionRAPDU) as e:
            ex.process_transaction(tx)
        assert e.value.status == Errors.WRONG_TRANSACTION_ID

