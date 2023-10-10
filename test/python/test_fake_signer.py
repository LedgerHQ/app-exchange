import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from ragger.utils import RAPDU
from ragger.error import ExceptionRAPDU

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors
from .apps.exchange_transaction_builder import get_partner_curve, craft_tx, encode_tx, extract_payout_ticker, extract_refund_ticker, ALL_SUBCOMMANDS, SWAP_SUBCOMMANDS, get_credentials
from .apps import cal as cal

from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER


SWAP_TX_INFOS = {
     "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
     "payin_extra_id": b"",
     "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
     "refund_extra_id": b"",
     "payout_address": b"bc1qer57ma0fzhqys2cmydhuj9cprf9eg0nw922a8j",
     "payout_extra_id": b"",
     "currency_from": "ETH",
     "currency_to": "BTC",
     "amount_to_provider": bytes.fromhex("013fc3a717fb5000"),
     "amount_to_wallet": b"\x0b\xeb\xc2\x00",
}

FUND_TX_INFOS = {
    "user_id": "John Wick",
    "account_name": "Remember Daisy",
    "in_currency": "ETH",
    "in_amount": b"\032\200\250]$T\000",
    "in_address": "0x252fb4acbe0de4f0bd2409a5ed59a71e4ef1d2bc"
}

SELL_TX_INFOS = {
    "trader_email": "john@doe.lost",
    "out_currency": "USD",
    "out_amount": {"coefficient": b"\x01", "exponent": 3},
    "in_currency": "ETH",
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

    @pytest.mark.parametrize("operation", ALL_SUBCOMMANDS)
    def test_fake_partner_credentials_sent(self, backend, operation):
        ex = ExchangeClient(backend, Rate.FIXED, operation)
        partner = SigningAuthority(curve=get_partner_curve(operation), name="partner")
        partner_fake = SigningAuthority(curve=get_partner_curve(operation), name="partner_fake")

        ex.init_transaction()
        credentials_fake = get_credentials(operation, partner_fake)
        credentials = get_credentials(operation, partner)
        ex.set_partner_key(credentials_fake)

        with pytest.raises(ExceptionRAPDU) as e:
            ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A PARTNER NOT SIGNED BY THE LEDGER KEY IS REFUSED

    @pytest.mark.parametrize("operation", ALL_SUBCOMMANDS)
    def test_fake_partner_credentials_signed(self, backend, operation):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, operation)
        partner = SigningAuthority(curve=get_partner_curve(operation), name="partner")

        ex.init_transaction()
        credentials = get_credentials(operation, partner)
        ex.set_partner_key(credentials)

        with pytest.raises(ExceptionRAPDU) as e:
            ex.check_partner_key(ledger_fake_signer.sign(credentials))
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A TRANSACTION INFORMATION NOT SIGNED BY THE PARTNER KEY IS REFUSED

    @pytest.mark.parametrize("operation", ALL_SUBCOMMANDS)
    def test_fake_transaction_infos(self, backend, operation):
        ex = ExchangeClient(backend, Rate.FIXED, operation)
        partner = SigningAuthority(curve=get_partner_curve(operation), name="partner")
        partner_fake = SigningAuthority(curve=get_partner_curve(operation), name="partner_fake")

        transaction_id = ex.init_transaction().data
        credentials = get_credentials(operation, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx = craft_tx(operation, TX_INFOS[operation], transaction_id)
        ex.process_transaction(tx, FEES)

        encoded_tx = encode_tx(operation, partner_fake, tx)
        with pytest.raises(ExceptionRAPDU) as e:
            ex.check_transaction_signature(encoded_tx)
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A COIN CONFIGURATION NOT SIGNED BY THE LEDGER KEY IS REFUSED

    @pytest.mark.parametrize("operation", ALL_SUBCOMMANDS)
    def test_fake_payout_coin_configuration(self, backend, operation):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, operation)
        partner = SigningAuthority(curve=get_partner_curve(operation), name="partner")

        transaction_id = ex.init_transaction().data
        credentials = get_credentials(operation, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx = craft_tx(operation, TX_INFOS[operation], transaction_id)
        ex.process_transaction(tx, FEES)
        encoded_tx = encode_tx(operation, partner, tx)
        ex.check_transaction_signature(encoded_tx)

        payout_ticker = extract_payout_ticker(operation, TX_INFOS[operation])
        payout_conf = cal.get_conf_for_ticker(payout_ticker, overload_signer=ledger_fake_signer)

        with pytest.raises(ExceptionRAPDU) as e:
            if operation == SubCommand.SWAP or operation == SubCommand.SWAP_NG:
                ex.check_payout_address(payout_conf)
            else:
                with ex.check_asset_in(payout_conf):
                    pass
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL

    @pytest.mark.parametrize("operation", SWAP_SUBCOMMANDS)
    def test_fake_refund_coin_configuration_swap(self, backend, operation):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, operation)
        partner = SigningAuthority(curve=get_partner_curve(operation), name="partner")

        transaction_id = ex.init_transaction().data
        credentials = get_credentials(operation, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx = craft_tx(operation, SWAP_TX_INFOS, transaction_id)
        ex.process_transaction(tx, FEES)
        encoded_tx = encode_tx(operation, partner, tx)
        ex.check_transaction_signature(encoded_tx)

        payout_conf = cal.get_conf_for_ticker(SWAP_TX_INFOS["currency_to"])
        refund_conf = cal.get_conf_for_ticker(SWAP_TX_INFOS["currency_from"], overload_signer=ledger_fake_signer)
        ex.check_payout_address(payout_conf)
        with pytest.raises(ExceptionRAPDU) as e:
            with ex.check_refund_address(refund_conf):
                pass
        assert e.value.status == Errors.SIGN_VERIFICATION_FAIL

