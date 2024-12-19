import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from ragger.utils import RAPDU
from ragger.error import ExceptionRAPDU

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors
from .apps.exchange_transaction_builder import get_partner_curve, ALL_SUBCOMMANDS, SWAP_SUBCOMMANDS, get_credentials, craft_and_sign_tx
from .apps import cal as cal

from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER

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


# Use a class to reuse the same Speculos instance
class TestFakeSigner:

    # CHECK THAT A PARTNER SIGNED BY THE LEDGER KEY BUT DIFFERENT THAN THE SET IS REFUSED

    @pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
    def test_fake_partner_credentials_sent(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="partner")
        partner_fake = SigningAuthority(curve=get_partner_curve(subcommand), name="partner_fake")

        ex.init_transaction()
        credentials_fake = get_credentials(subcommand, partner_fake)
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials_fake)

        with pytest.raises(ExceptionRAPDU) as e:
            ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A PARTNER NOT SIGNED BY THE LEDGER KEY IS REFUSED

    @pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
    def test_fake_partner_credentials_signed(self, backend, subcommand):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="partner")

        ex.init_transaction()
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)

        with pytest.raises(ExceptionRAPDU) as e:
            ex.check_partner_key(ledger_fake_signer.sign(credentials))
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A TRANSACTION INFORMATION NOT SIGNED BY THE PARTNER KEY IS REFUSED

    @pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
    def test_fake_transaction_infos(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="partner")
        partner_fake = SigningAuthority(curve=get_partner_curve(subcommand), name="partner_fake")

        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner_fake)
        ex.process_transaction(tx)

        with pytest.raises(ExceptionRAPDU) as e:
            ex.check_transaction_signature(tx_signature)
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A COIN CONFIGURATION NOT SIGNED BY THE LEDGER KEY IS REFUSED

    @pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
    def test_fake_payout_coin_configuration(self, backend, subcommand):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="partner")

        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        with pytest.raises(ExceptionRAPDU) as e:
            if subcommand == SubCommand.SWAP or subcommand == SubCommand.SWAP_NG:
                ex.check_payout_address(CURRENCY_TO.get_conf_for_ticker(overload_signer=ledger_fake_signer))
            else:
                with ex.check_asset_in(CURRENCY_FROM.get_conf_for_ticker(overload_signer=ledger_fake_signer)):
                    pass
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL

    @pytest.mark.parametrize("subcommand", SWAP_SUBCOMMANDS)
    def test_fake_refund_coin_configuration_swap(self, backend, subcommand):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="partner")

        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        ex.check_payout_address(CURRENCY_TO.get_conf_for_ticker())
        with pytest.raises(ExceptionRAPDU) as e:
            with ex.check_refund_address(CURRENCY_FROM.get_conf_for_ticker(overload_signer=ledger_fake_signer)):
                pass
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL

