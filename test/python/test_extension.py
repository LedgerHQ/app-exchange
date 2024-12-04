import pytest

from ragger.utils import RAPDU, prefix_with_len, create_currency_config
from ragger.error import ExceptionRAPDU

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors, Command, P2_EXTEND, P2_MORE, EXCHANGE_CLASS
from .apps.exchange_transaction_builder import get_partner_curve, LEGACY_SUBCOMMANDS, ALL_SUBCOMMANDS, NEW_SUBCOMMANDS, get_credentials, craft_and_sign_tx
from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER
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

class TestExtension:

    @pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
    def test_extension_forbidden_for_command(self, backend, subcommand):
        for ext in [P2_MORE, P2_EXTEND, (P2_EXTEND | P2_MORE)]:
            with pytest.raises(ExceptionRAPDU) as e:
                backend.exchange(EXCHANGE_CLASS, Command.START_NEW_TRANSACTION, p1=Rate.FIXED, p2=(subcommand | ext), data=b"")
            assert e.value.status == Errors.WRONG_P2_EXTENSION


    @pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
    def test_extension_many_chunks(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)

        # Artificially create many chunks to test the TX concatenation
        tx_split = [tx[x:x + 70] for x in range(0, len(tx), 70)]
        for i, p in enumerate(tx_split):
            p2 = subcommand
            if i != len(tx_split) - 1:
                p2 |= P2_MORE
            if i != 0:
                p2 |= P2_EXTEND
            backend.exchange(EXCHANGE_CLASS, Command.PROCESS_TRANSACTION_RESPONSE, p1=Rate.FIXED, p2=p2, data=p)
        ex.check_transaction_signature(tx_signature)


    @pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
    def test_extension_advanced_usage(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)

        # Start with an EXTEND flag
        with pytest.raises(ExceptionRAPDU) as e:
            backend.exchange(EXCHANGE_CLASS, Command.PROCESS_TRANSACTION_RESPONSE, p1=Rate.FIXED, p2=(subcommand | P2_EXTEND | P2_MORE), data=b"")
        assert e.value.status == Errors.INVALID_P2_EXTENSION

        # Previous APDU must has been dropped, ensure the P2_MORE was not taken into account
        with pytest.raises(ExceptionRAPDU) as e:
            backend.exchange(EXCHANGE_CLASS, Command.PROCESS_TRANSACTION_RESPONSE, p1=Rate.FIXED, p2=(subcommand | P2_EXTEND), data=b"")
        assert e.value.status == Errors.INVALID_P2_EXTENSION

        # Start a chunk send with wrong data
        backend.exchange(EXCHANGE_CLASS, Command.PROCESS_TRANSACTION_RESPONSE, p1=Rate.FIXED, p2=(subcommand | P2_MORE), data=b"0011233445566778899")

        # Restart a chunk send with correct data, artificially create many chunks to test the TX concatenation
        tx_split = [tx[x:x + 70] for x in range(0, len(tx), 70)]
        for i, p in enumerate(tx_split):
            p2 = subcommand
            if i != len(tx_split) - 1:
                p2 |= P2_MORE
            if i != 0:
                p2 |= P2_EXTEND
            backend.exchange(EXCHANGE_CLASS, Command.PROCESS_TRANSACTION_RESPONSE, p1=Rate.FIXED, p2=p2, data=p)

        # Check the signature to ensure the data received has not been corrupted
        ex.check_transaction_signature(tx_signature)
