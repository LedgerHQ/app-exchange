import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from ragger.utils import RAPDU
from ragger.backend import RaisePolicy

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors
from .apps.exchange_transaction_builder import get_partner_curve, craft_tx, encode_tx, extract_payout_ticker, extract_refund_ticker
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
    SubCommand.FUND: FUND_TX_INFOS,
    SubCommand.SELL: SELL_TX_INFOS,
}

FEES = 100


# Use a class to reuse the same Speculos instance
class TestFakeSigner:

    # CHECK THAT A PARTNER SIGNED BY THE LEDGER KEY BUT DIFFERENT THAN THE SET IS REFUSED

    @pytest.mark.parametrize("operation", [SubCommand.SWAP, SubCommand.FUND, SubCommand.SELL])
    def test_fake_partner_credentials_sent(self, backend, operation):
        ex = ExchangeClient(backend, Rate.FIXED, operation)
        partner = SigningAuthority(curve=get_partner_curve(operation), name="partner")
        partner_fake = SigningAuthority(curve=get_partner_curve(operation), name="partner_fake")

        ex.init_transaction()
        ex.set_partner_key(partner_fake.credentials)

        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        assert rapdu.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A PARTNER NOT SIGNED BY THE LEDGER KEY IS REFUSED

    @pytest.mark.parametrize("operation", [SubCommand.SWAP, SubCommand.FUND, SubCommand.SELL])
    def test_fake_partner_credentials_signed(self, backend, operation):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, operation)
        partner = SigningAuthority(curve=get_partner_curve(operation), name="partner")

        ex.init_transaction()
        ex.set_partner_key(partner.credentials)

        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.check_partner_key(ledger_fake_signer.sign(partner.credentials))
        assert rapdu.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A TRANSACTION INFORMATION NOT SIGNED BY THE PARTNER KEY IS REFUSED

    @pytest.mark.parametrize("operation", [SubCommand.SWAP, SubCommand.FUND, SubCommand.SELL])
    def test_fake_transaction_infos(self, backend, operation):
        ex = ExchangeClient(backend, Rate.FIXED, operation)
        partner = SigningAuthority(curve=get_partner_curve(operation), name="partner")
        partner_fake = SigningAuthority(curve=get_partner_curve(operation), name="partner_fake")

        transaction_id = ex.init_transaction().data
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        tx = craft_tx(operation, TX_INFOS[operation], transaction_id)
        ex.process_transaction(tx, FEES)

        encoded_tx = encode_tx(operation, partner_fake, tx)
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.check_transaction_signature(encoded_tx)
        assert rapdu.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A COIN CONFIGURATION NOT SIGNED BY THE LEDGER KEY IS REFUSED

    @pytest.mark.parametrize("operation", [SubCommand.SWAP, SubCommand.FUND, SubCommand.SELL])
    def test_fake_payout_coin_configuration(self, backend, operation):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, operation)
        partner = SigningAuthority(curve=get_partner_curve(operation), name="partner")

        transaction_id = ex.init_transaction().data
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        tx = craft_tx(operation, TX_INFOS[operation], transaction_id)
        ex.process_transaction(tx, FEES)
        encoded_tx = encode_tx(operation, partner, tx)
        ex.check_transaction_signature(encoded_tx)

        payout_ticker = extract_payout_ticker(operation, TX_INFOS[operation])
        payout_conf = cal.get_conf_for_ticker(payout_ticker, overload_signer=ledger_fake_signer)
        refund_ticker = extract_refund_ticker(operation, TX_INFOS[operation])
        refund_conf = cal.get_conf_for_ticker(refund_ticker)
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        with ex.check_address(payout_conf, refund_conf):
            pass
        assert ex.get_check_address_response().status == Errors.SIGN_VERIFICATION_FAIL

    def test_fake_refund_coin_configuration_swap(self, backend):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP), name="partner")

        transaction_id = ex.init_transaction().data
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        tx = craft_tx(SubCommand.SWAP, SWAP_TX_INFOS, transaction_id)
        ex.process_transaction(tx, FEES)
        encoded_tx = encode_tx(SubCommand.SWAP, partner, tx)
        ex.check_transaction_signature(encoded_tx)

        payout_conf = cal.get_conf_for_ticker(SWAP_TX_INFOS["currency_to"])
        refund_conf = cal.get_conf_for_ticker(SWAP_TX_INFOS["currency_from"], overload_signer=ledger_fake_signer)
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        with ex.check_address(payout_conf, refund_conf):
            pass
        assert ex.get_check_address_response().status == Errors.SIGN_VERIFICATION_FAIL

