import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from ragger.utils import RAPDU
from ragger.backend import RaisePolicy

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors

from .signing_authority import SigningAuthority, LEDGER_SIGNER


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
    "SWAP": SWAP_TX_INFOS,
    "FUND": FUND_TX_INFOS,
    "SELL": SELL_TX_INFOS,
}
SUB_COMMAND = {
    "SWAP": SubCommand.SWAP,
    "FUND": SubCommand.FUND,
    "SELL": SubCommand.SELL,
}

FEES = 100


# Use a class to reuse the same Speculos instance
class TestFakeSigner:

    # CHECK THAT A PARTNER SIGNED BY THE LEDGER KEY BUT DIFFERENT THAN THE SET IS REFUSED

    @pytest.mark.parametrize("operation", ["SWAP", "FUND", "SELL"])
    def test_fake_partner_credentials_sent(self, backend, operation):
        ex = ExchangeClient(backend, Rate.FIXED, SUB_COMMAND[operation])
        partner = SigningAuthority(curve=ex.partner_curve, name="partner")
        partner_fake = SigningAuthority(curve=ex.partner_curve, name="partner_fake")

        ex.init_transaction()
        ex.set_partner_key(partner_fake.credentials)

        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        assert rapdu.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A PARTNER NOT SIGNED BY THE LEDGER KEY IS REFUSED

    @pytest.mark.parametrize("operation", ["SWAP", "FUND", "SELL"])
    def test_fake_partner_credentials_signed(self, backend, operation):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, SUB_COMMAND[operation])
        partner = SigningAuthority(curve=ex.partner_curve, name="partner")

        ex.init_transaction()
        ex.set_partner_key(partner.credentials)

        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.check_partner_key(ledger_fake_signer.sign(partner.credentials))
        assert rapdu.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A TRANSACTION INFORMATION NOT SIGNED BY THE PARTNER KEY IS REFUSED

    @pytest.mark.parametrize("operation", ["SWAP", "FUND", "SELL"])
    def test_fake_transaction_infos(self, backend, operation):
        ex = ExchangeClient(backend, Rate.FIXED, SUB_COMMAND[operation])
        partner = SigningAuthority(curve=ex.partner_curve, name="partner")
        partner_fake = SigningAuthority(curve=ex.partner_curve, name="partner_fake")

        ex.init_transaction()
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        ex.process_transaction(TX_INFOS[operation], FEES)

        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.check_transaction_signature(partner_fake)
        assert rapdu.status == Errors.SIGN_VERIFICATION_FAIL


    # CHECK THAT A COIN CONFIGURATION NOT SIGNED BY THE LEDGER KEY IS REFUSED

    @pytest.mark.parametrize("operation", ["FUND", "SELL"])
    def test_fake_payout_coin_configuration(self, backend, operation):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, SUB_COMMAND[operation])
        partner = SigningAuthority(curve=ex.partner_curve, name="partner")

        ex.init_transaction()
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        ex.process_transaction(TX_INFOS[operation], FEES)
        ex.check_transaction_signature(partner)

        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        with ex.check_address(payout_signer=ledger_fake_signer):
            pass
        assert ex.get_check_address_response().status == Errors.SIGN_VERIFICATION_FAIL

    def test_fake_payout_coin_configuration_swap(self, backend):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name="partner")

        ex.init_transaction()
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        ex.process_transaction(SWAP_TX_INFOS, FEES)
        ex.check_transaction_signature(partner)

        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        with ex.check_address(payout_signer=ledger_fake_signer, refund_signer=LEDGER_SIGNER):
            pass
        assert ex.get_check_address_response().status == Errors.SIGN_VERIFICATION_FAIL

    def test_fake_refund_coin_configuration_swap(self, backend):
        ledger_fake_signer = SigningAuthority(curve=ec.SECP256K1(), name="fake_signer")
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name="partner")

        ex.init_transaction()
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        ex.process_transaction(SWAP_TX_INFOS, FEES)
        ex.check_transaction_signature(partner)

        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=ledger_fake_signer):
            pass
        assert ex.get_check_address_response().status == Errors.SIGN_VERIFICATION_FAIL

