import pytest
from dataclasses import dataclass
from ragger.utils import prefix_with_len
from ragger.error import ExceptionRAPDU
from typing import Optional

from ledger_app_clients.exchange.client import ExchangeClient, Rate, SubCommand, Errors
from .apps.litecoin import LitecoinClient

from ledger_app_clients.exchange.signing_authority import SigningAuthority, LEDGER_SIGNER
from ledger_app_clients.exchange.transaction_builder import get_partner_curve, craft_and_sign_tx, ALL_SUBCOMMANDS, get_credentials
from .apps import cal as cal
from ledger_app_clients.exchange.utils import handle_lib_call_start_or_stop

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
     "amount_to_provider": bytes.fromhex("01"),
     "amount_to_wallet": bytes.fromhex("01"),
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


class TestTrustedName:

    @pytest.mark.parametrize("subcommand", [SubCommand.SWAP, SubCommand.SWAP_NG])
    def test_trusted_name_wrong_challenge(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        challenge = ex.get_challenge().data
        assert len(challenge) == 4
        wrong_challenge = challenge[:-1] + bytes([challenge[-1] + 1])
        with pytest.raises(ExceptionRAPDU) as e:
            ex.send_pki_certificate_and_trusted_name_descriptor(challenge=wrong_challenge)
        assert e.value.status == Errors.WRONG_TLV_CHALLENGE
        # Ensure reroll happened
        with pytest.raises(ExceptionRAPDU) as e:
            ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge)
        assert e.value.status == Errors.WRONG_TLV_CHALLENGE

    @pytest.mark.parametrize("subcommand", [SubCommand.SWAP, SubCommand.SWAP_NG])
    @pytest.mark.parametrize("field_to_test", ["payout_address", "refund_address"])
    @pytest.mark.parametrize("value", [b"0xcafedeca", b"f" * 64])
    def test_trusted_name_valid(self, backend, subcommand, field_to_test, value):
        if subcommand == SubCommand.SWAP and len(value) > 50:
            pytest.skip("Can't test max address value on legacy flows")
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))

        tx_infos = TX_INFOS[subcommand].copy()
        actual_address = tx_infos[field_to_test]
        temp_address = value
        print(f"Replacing {actual_address} by {temp_address}")
        tx_infos[field_to_test] = temp_address
        tx, tx_signature = craft_and_sign_tx(subcommand, tx_infos, transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        challenge = ex.get_challenge().data
        ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, trusted_name=temp_address, address=actual_address)
        ex.check_payout_address(CURRENCY_TO.get_conf_for_ticker())
        ex.check_refund_address_no_display(CURRENCY_FROM.get_conf_for_ticker())

    def test_trusted_name_no_match(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP_NG)
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP_NG), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(SubCommand.SWAP_NG, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))

        tx, tx_signature = craft_and_sign_tx(SubCommand.SWAP_NG, TX_INFOS[SubCommand.SWAP_NG], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        challenge = ex.get_challenge().data
        with pytest.raises(ExceptionRAPDU) as e:
            ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, trusted_name=b"0xcafedeca", address=b"0xcafedeca")
        assert e.value.status == Errors.DESCRIPTOR_NOT_USED

    @pytest.mark.parametrize("subcommand", [SubCommand.SELL, SubCommand.SELL_NG, SubCommand.FUND, SubCommand.FUND_NG])
    def test_trusted_name_invalid_subcommand(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")

        transaction_id = ex.init_transaction().data

        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        with pytest.raises(ExceptionRAPDU) as e:
            ex.get_challenge()
        assert e.value.status == Errors.INVALID_INSTRUCTION
        with pytest.raises(ExceptionRAPDU) as e:
            ex.send_pki_certificate_and_trusted_name_descriptor()
        assert e.value.status == Errors.INVALID_INSTRUCTION

    @pytest.mark.parametrize("subcommand", [SubCommand.SWAP, SubCommand.SWAP_NG])
    def test_trusted_name_missing_field(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        for skip in ["structure_type", "version", "trusted_name_type", "trusted_name_source", "trusted_name", "chain_id", "address", "challenge", "signer_key_id", "signer_algo", "der_signature"]:
            with pytest.raises(ExceptionRAPDU) as e:
                if skip == "structure_type":
                    ex.send_pki_certificate_and_trusted_name_descriptor(structure_type=None)
                elif skip == "version":
                    ex.send_pki_certificate_and_trusted_name_descriptor(version=None)
                elif skip == "trusted_name_type":
                    ex.send_pki_certificate_and_trusted_name_descriptor(trusted_name_type=None)
                elif skip == "trusted_name_source":
                    ex.send_pki_certificate_and_trusted_name_descriptor(trusted_name_source=None)
                elif skip == "trusted_name":
                    ex.send_pki_certificate_and_trusted_name_descriptor(trusted_name=None)
                elif skip == "chain_id":
                    ex.send_pki_certificate_and_trusted_name_descriptor(chain_id=None)
                elif skip == "address":
                    ex.send_pki_certificate_and_trusted_name_descriptor(address=None)
                elif skip == "challenge":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=None)
                elif skip == "signer_key_id":
                    ex.send_pki_certificate_and_trusted_name_descriptor(signer_key_id=None)
                elif skip == "signer_algo":
                    ex.send_pki_certificate_and_trusted_name_descriptor(signer_algo=None)
                elif skip == "der_signature":
                    ex.send_pki_certificate_and_trusted_name_descriptor(skip_signature_field=True)
            assert e.value.status == Errors.MISSING_TLV_CONTENT or e.value.status == Errors.WRONG_TRUSTED_NAME_TLV

    @pytest.mark.parametrize("subcommand", [SubCommand.SWAP, SubCommand.SWAP_NG])
    def test_trusted_name_wrong_field(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        for fake in ["structure_type", "version", "trusted_name_type"]:
            challenge = ex.get_challenge().data
            with pytest.raises(ExceptionRAPDU) as e:
                if fake == "structure_type":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, structure_type=0)
                elif fake == "version":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, version=0)
                elif fake == "trusted_name_type":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, trusted_name_type=0)
            assert e.value.status == Errors.WRONG_TLV_CONTENT or e.value.status == Errors.WRONG_TRUSTED_NAME_TLV

        with pytest.raises(ExceptionRAPDU) as e:
            challenge = ex.get_challenge().data
            ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, signer_key_id=0x9)
        assert e.value.status == Errors.WRONG_TRUSTED_NAME_TLV

        with pytest.raises(ExceptionRAPDU) as e:
            challenge = ex.get_challenge().data
            ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, fake_signature_field=True)
        assert e.value.status == Errors.WRONG_TRUSTED_NAME_TLV

        for fake in ["trusted_name", "address"]:
            challenge = ex.get_challenge().data
            with pytest.raises(ExceptionRAPDU) as e:
                if fake == "trusted_name":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, trusted_name=b"")
                elif fake == "address":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, address=b"")
            assert e.value.status == Errors.WRONG_TRUSTED_NAME_TLV or e.value.status == Errors.WRONG_TLV_CONTENT


# Needs to be in a separate Speculos start
class TestTrustedNameNoCertificate:

    @pytest.mark.parametrize("subcommand", [SubCommand.SWAP, SubCommand.SWAP_NG])
    def test_trusted_name_no_pki_load(self, backend, subcommand):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        with pytest.raises(ExceptionRAPDU) as e:
            challenge = ex.get_challenge().data
            ex.send_trusted_name_descriptor(challenge=challenge)
        assert e.value.status == Errors.WRONG_TRUSTED_NAME_TLV
