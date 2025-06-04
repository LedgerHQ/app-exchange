import pytest
import copy

from cryptography.hazmat.primitives.asymmetric import ec

from ledger_app_clients.exchange.client import ExchangeClient, Rate, SubCommand
from ledger_app_clients.exchange.transaction_builder import SWAP_NG_SPECS, SELL_NG_SPECS, FUND_NG_SPECS, get_partner_curve, get_credentials, craft_and_sign_tx, SignatureComputation, SignatureEncoding, PayloadEncoding
from ledger_app_clients.exchange.signing_authority import SigningAuthority, LEDGER_SIGNER

# Some valid infos for TX. Content is irrelevant for the test

SWAP_TX_INFOS = {
     "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
     "payin_extra_id": b"",
     "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
     "refund_extra_id": b"",
     "payout_address": b"bc1qqtl9jlrwcr3fsfcjj2du7pu6fcgaxl5dsw2vyg",
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
    SubCommand.SWAP_NG: SWAP_TX_INFOS,
    SubCommand.FUND_NG: FUND_TX_INFOS,
    SubCommand.SELL_NG: SELL_TX_INFOS,
}
TEST_NAME_SUFFIX = {
    SubCommand.SWAP_NG: "swap_ng",
    SubCommand.FUND_NG: "fund_ng",
    SubCommand.SELL_NG: "sell_ng",
}
FEES = 100

class TestNGConfiguration:

    @pytest.mark.parametrize("specs_param", [SWAP_NG_SPECS, SELL_NG_SPECS, FUND_NG_SPECS], ids=["swap_ng", "sell_ng", "fund_ng"])
    @pytest.mark.parametrize("payload_encoding", [PayloadEncoding.BASE_64_URL, PayloadEncoding.BYTES_ARRAY], ids=["base_56", "b_array"])
    @pytest.mark.parametrize("signature_encoding", [SignatureEncoding.PLAIN_R_S, SignatureEncoding.DER], ids=["R,S", "DER"])
    @pytest.mark.parametrize("signature_computation", [SignatureComputation.DOT_PREFIXED_BASE_64_URL, SignatureComputation.BINARY_ENCODED_PAYLOAD], ids=["dot_prefixed", "not_prefixed"])
    def test_ng_tx_configuration(self, backend, specs_param, payload_encoding, signature_encoding, signature_computation):
        specs = copy.deepcopy(specs_param)
        specs.payload_encoding = payload_encoding
        specs.signature_encoding = signature_encoding
        specs.signature_computation = signature_computation

        tx_infos = TX_INFOS[specs.subcommand_id]

        ex = ExchangeClient(backend, Rate.FIXED, specs.subcommand_id)
        partner = SigningAuthority(curve=get_partner_curve(specs.subcommand_id), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(specs.subcommand_id, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(specs, TX_INFOS[specs.subcommand_id], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)


    @pytest.mark.parametrize("specs_param", [SWAP_NG_SPECS, SELL_NG_SPECS, FUND_NG_SPECS], ids=["swap_ng", "sell_ng", "fund_ng"])
    @pytest.mark.parametrize("partner_curve", [ec.SECP256R1(), ec.SECP256K1()], ids=["R1", "K1"])
    def test_ng_curve_configuration(self, backend, specs_param, partner_curve):
        specs = copy.deepcopy(specs_param)
        specs.partner_curve = partner_curve

        tx_infos = TX_INFOS[specs.subcommand_id]

        ex = ExchangeClient(backend, Rate.FIXED, specs.subcommand_id)
        partner = SigningAuthority(curve=get_partner_curve(specs.subcommand_id), name="Name")
        transaction_id = ex.init_transaction().data
        credentials = get_credentials(specs.subcommand_id, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx, tx_signature = craft_and_sign_tx(specs, TX_INFOS[specs.subcommand_id], transaction_id, FEES, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)
