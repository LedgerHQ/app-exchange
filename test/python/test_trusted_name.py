import pytest
from dataclasses import dataclass
from ragger.utils import prefix_with_len
from ragger.error import ExceptionRAPDU
from typing import Optional

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors
from .apps.litecoin import LitecoinClient

from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps.exchange_transaction_builder import get_partner_curve, craft_and_sign_tx, ALL_SUBCOMMANDS, get_credentials
from .apps import cal as cal
from .utils import handle_lib_call_start_or_stop

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
        assert e.value.status == Errors.WRONG_CHALLENGE
        # Ensure reroll happened
        with pytest.raises(ExceptionRAPDU) as e:
            ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge)
        assert e.value.status == Errors.WRONG_CHALLENGE

    @pytest.mark.parametrize("subcommand", [SubCommand.SWAP, SubCommand.SWAP_NG])
    @pytest.mark.parametrize("field_to_test", ["payout_address", "refund_address"])
    @pytest.mark.parametrize("value", [b"0xcafedeca", b"f" * 150])
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
            assert e.value.status == Errors.MISSING_TLV_CONTENT

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

        for fake in ["structure_type", "version", "trusted_name_type", "trusted_name_source", "signer_algo"]:
            challenge = ex.get_challenge().data
            with pytest.raises(ExceptionRAPDU) as e:
                if fake == "structure_type":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, structure_type=0)
                elif fake == "version":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, version=0)
                elif fake == "trusted_name_type":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, trusted_name_type=0)
                elif fake == "trusted_name_source":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, trusted_name_source=0)
                elif fake == "signer_algo":
                    ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, signer_algo=0)
            assert e.value.status == Errors.WRONG_TLV_CONTENT

        with pytest.raises(ExceptionRAPDU) as e:
            challenge = ex.get_challenge().data
            ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, signer_key_id=0x9)
        assert e.value.status == Errors.WRONG_TLV_KEY_ID

        with pytest.raises(ExceptionRAPDU) as e:
            challenge = ex.get_challenge().data
            ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, fake_signature_field=True)
        assert e.value.status == Errors.WRONG_TLV_SIGNATURE

        for fake in ["trusted_name", "address"]:
            values = [b""]
            if subcommand == SubCommand.SWAP_NG:
                values += [b"F"*151]
            for value in values:
                challenge = ex.get_challenge().data
                with pytest.raises(ExceptionRAPDU) as e:
                    if fake == "trusted_name":
                        ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, trusted_name=value)
                    elif fake == "address":
                        ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, address=value)
                assert e.value.status == Errors.WRONG_TLV_FORMAT


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
        assert e.value.status == Errors.NO_CERTIFICATE_LOADED

# def test_custom(backend):
#     backend.exchange_raw(bytes.fromhex("e003000300"))
#     backend.exchange_raw(bytes.fromhex("e0040003500d544553542d50524f5649444552000478d5facdae2305f48795d3ce7d9244f5060d2f800901da5746d1f4177ae8d7bbe63f3870efc0d36af8f91962811e1d8d9df91ce3b3ea2cd9f550c7d465f8b7b3"))
#     backend.exchange_raw(bytes.fromhex("e0050003483046022100ddff28e84aaee65238bfbd095e2be47597d76c0cfb1ae637cb2f6b3e6658994c022100d899d82d4855e92a9f1c34866edb2ae34603f9735ef9dfa6caf7a18d5ba4c260"))
#     backend.exchange_raw(bytes.fromhex("e0060023ff01010043696f7765444e6d4d6d4a6a4d546c455a6a68444e6b4e6b4f454a684d544933595451774d6a466b4d5449334f45457a4d6d4d78517a597a4e5451614b6a42344e6a5a6a4e444d334d5746464f455a475a5551795a574d78597a4a46516d4a6959304e6d596a64464e446b304d546778525446464d796f734e6d67794d546855634664475348427059576f3255475a6c4f47633555587033636d4a475255784f56564e5a636d464f51576c56615646744d553436413056555345494556564e4551306f4831536d756e6f594141464943433768694944554b366779583930667830506467675559557048556a674273613633304c7937716970505272"))
#     backend.exchange_raw(bytes.fromhex("e00600130c2d42684c0701f921cb3ae048"))
#     backend.exchange_raw(bytes.fromhex("e0070003420101f5190278a5b9a434f69e251b7a2f7b6ca70335cbaa1138e509b225d6e5922a07ee927b37d4937249967b04299fb45c9866e2063bb0fbc13f72249c456deb2934"))
#     # backend.exchange_raw(bytes.fromhex("b0060400a001010102010235010536010110040105000013020002140101200c747275737465645f6e616d65300200073101043201213401013321036a94e7a42cd0c33fdf440c8e2ab2542cefbe5db7aa0b93a9fc814b9acfa75eb415473045022100a9a018f7a1e66dd0d511aafe115741fadaae892cb2cb37158ff33ee01a10128602204d0a2ef7ca5516e84decf08928508e730a0597546a821a81475ffb5325713d17"))
#     backend.exchange_raw(bytes.fromhex("e010000300"))
#     backend.exchange_raw(bytes.fromhex("e0110003ed010103020102700106710106202c366832313854705746487069616a36506665386739517a77726246454c4e55535972614e41695569516d314e230165222c36334d376b504a764c734734366a6252325a7269455538787750716b4d4e4b4e6f4242513436706f6262766f732c45506a465764643541756671535371654d32714e31787a7962617043384734774547476b5a7779544474317612046c7e5dce13010714010115463044022051cedd8fb6900c0cf752be4e9a8dad95c6f4d68abfb70329abaab0270ae64507022073d685f7f7a055bf20d50ed772c4c913b09be7002022c76a7627ddddb4a8ca50"))
#     backend.exchange_raw(bytes.fromhex("e00800036813045553444306536f6c616e61060455534443063044022025169f3f8ede05c55735b3a067753c4763e54161e80f31155cce7e6edf34fda202201458433d08c9b8c065d5f0b4bb83d6bdbff4caadc04a4836462573782ec6471c0d038000002c800001f580000001"))
