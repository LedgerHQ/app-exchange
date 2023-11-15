import pytest
from time import sleep
from ragger.backend import RaisePolicy
from ragger.utils import pack_APDU, RAPDU
from ragger.error import ExceptionRAPDU
from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.ethereum import EthereumClient, ERR_SILENT_MODE_CHECK_FAILED, eth_amount_to_wei

from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps.exchange_transaction_builder import get_partner_curve, extract_payout_ticker, extract_refund_ticker, craft_and_sign_tx
from .apps import cal as cal


def prepare_exchange(backend, exchange_navigation_helper, amount: str):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP), name="Default name")

    transaction_id = ex.init_transaction().data
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
        "payin_extra_id": b"",
        "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "refund_extra_id": b"",
        "payout_address": b"bc1qqtl9jlrwcr3fsfcjj2du7pu6fcgaxl5dsw2vyg",
        "payout_extra_id": b"",
        "currency_from": "ETH",
        "currency_to": "BTC",
        "amount_to_provider": bytes.fromhex(amount),
        "amount_to_wallet": b"\x0b\xeb\xc2\x00",
    }
    fees = eth_amount_to_wei(0.000588)

    tx, tx_signature = craft_and_sign_tx(SubCommand.SWAP, tx_infos, transaction_id, fees, partner)
    ex.process_transaction(tx)
    ex.check_transaction_signature(tx_signature)

    payout_ticker = extract_payout_ticker(SubCommand.SWAP, tx_infos)
    refund_ticker = extract_refund_ticker(SubCommand.SWAP, tx_infos)
    ex.check_payout_address(cal.get_conf_for_ticker(payout_ticker))
    with ex.check_refund_address(cal.get_conf_for_ticker(refund_ticker)):
        exchange_navigation_helper.simple_accept()
    ex.start_signing_transaction()


def test_swap_eth_to_btc_wrong_amount(backend, exchange_navigation_helper):
    amount       = '013fc3a717fb5000'
    wrong_amount = '013fc3a6be932100'
    prepare_exchange(backend, exchange_navigation_helper, amount)
    eth = EthereumClient(backend, derivation_path=bytes.fromhex("058000002c8000003c800000000000000000000000"))
    eth.get_public_key()
    try:
        backend.raise_policy = RaisePolicy.RAISE_ALL
        eth.sign(extra_payload=bytes.fromhex("ec09850684ee180082520894d692cb1346262f584d17b4b470954501f6715a8288" + wrong_amount + "80018080"))
    except ExceptionRAPDU as rapdu:
        assert rapdu.status == ERR_SILENT_MODE_CHECK_FAILED.status, f"Received APDU status {hex(rapdu.status)}, expected {hex(ERR_SILENT_MODE_CHECK_FAILED.status)}"


def test_swap_eth_to_btc_ok(backend, exchange_navigation_helper):
    amount = '013fc3a717fb5000'
    prepare_exchange(backend, exchange_navigation_helper, amount)
    sleep(1)
    eth = EthereumClient(backend, derivation_path=bytes.fromhex("058000002c8000003c800000000000000000000000"))
    sleep(1)
    eth.get_public_key()
    sleep(1)
    eth.sign(extra_payload=bytes.fromhex("ec09850684ee180082520894d692cb1346262f584d17b4b470954501f6715a8288" + amount + "80018080"))
