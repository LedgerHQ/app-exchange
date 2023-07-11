import pytest
from time import sleep

from ragger.backend import RaisePolicy
from ragger.utils import pack_APDU, RAPDU
from ragger.error import ExceptionRAPDU

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors
from .apps.ethereum import EthereumClient, ERR_SILENT_MODE_CHECK_FAILED, eth_amount_to_wei_hex_string, eth_amount_to_wei

from .apps.solana import SolanaClient, ErrorType
from .apps.solana_utils import SOL_PACKED_DERIVATION_PATH
from .apps.solana_cmd_builder import SystemInstructionTransfer, Message, verify_signature
from .apps import solana_utils as SOL

from .signing_authority import SigningAuthority, LEDGER_SIGNER


ETH_AMOUNT = eth_amount_to_wei_hex_string(0.09000564)
ETH_FEES = eth_amount_to_wei(0.000588)

FOREIGN_ETH_ADDRESS = b"0xd692Cb1346262F584D17B4B470954501f6715a82"
OWNED_ETH_ADDRESS = b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D"


# Swap transaction infos for valid ETH <-> SOL exchanges. Tamper the values to generate errors
VALID_SWAP_ETH_TO_SOL_TX_INFOS = {
    "payin_address": FOREIGN_ETH_ADDRESS,
    "payin_extra_id": b"",
    "refund_address": OWNED_ETH_ADDRESS,
    "refund_extra_id": b"",
    "payout_address": SOL.OWNED_ADDRESS,
    "payout_extra_id": b"",
    "currency_from": "ETH",
    "currency_to": "SOL",
    "amount_to_provider": bytes.fromhex(ETH_AMOUNT),
    "amount_to_wallet": SOL.AMOUNT_BYTES,
}

VALID_SWAP_SOL_TO_ETH_TX_INFOS = {
    "payin_address": SOL.FOREIGN_ADDRESS,
    "payin_extra_id": b"",
    "refund_address": SOL.OWNED_ADDRESS,
    "refund_extra_id": b"",
    "payout_address": OWNED_ETH_ADDRESS,
    "payout_extra_id": b"",
    "currency_from": "SOL",
    "currency_to": "ETH",
    "amount_to_provider": SOL.AMOUNT_BYTES,
    "amount_to_wallet": bytes.fromhex(ETH_AMOUNT),
}

# Helper to validate a SWAP transaction by the Exchange app and put the Solana app in front
def valid_swap(backend, exchange_navigation_helper, tx_infos, fees):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tx_infos, fees)
    ex.check_transaction_signature(partner)
    with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER):
        exchange_navigation_helper.simple_accept()
    ex.start_signing_transaction()


# Validate regular ETH <-> SOL exchanges

def test_solana_swap_recipient_ok(backend, exchange_navigation_helper):
    valid_swap(backend, exchange_navigation_helper, VALID_SWAP_ETH_TO_SOL_TX_INFOS, ETH_FEES)

    eth = EthereumClient(backend, derivation_path=bytes.fromhex("058000002c8000003c800000000000000000000000"))
    eth.get_public_key()
    eth.sign(extra_payload=bytes.fromhex("ec09850684ee180082520894d692cb1346262f584d17b4b470954501f6715a8288" + ETH_AMOUNT + "80018080"))

def test_solana_swap_sender_ok(backend, exchange_navigation_helper):
    valid_swap(backend, exchange_navigation_helper, VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(backend)
    with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
        pass
    signature: bytes = sol.get_async_response().data
    verify_signature(SOL.OWNED_PUBLIC_KEY, message, signature)

def test_solana_swap_sender_double_sign(backend, exchange_navigation_helper):
    valid_swap(backend, exchange_navigation_helper, VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(backend)
    with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
        pass
    signature: bytes = sol.get_async_response().data
    verify_signature(SOL.OWNED_PUBLIC_KEY, message, signature)

    sleep(0.5)

    with pytest.raises(ExceptionRAPDU) as e:
        with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
            pass
    assert e.value.status == Errors.INVALID_INSTRUCTION

# Validate canceled ETH <-> SOL exchanges

def test_solana_swap_recipient_cancel(backend, exchange_navigation_helper):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(VALID_SWAP_ETH_TO_SOL_TX_INFOS, ETH_FEES)
    ex.check_transaction_signature(partner)

    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER):
        exchange_navigation_helper.simple_reject()
    assert ex.get_check_address_response().status == Errors.USER_REFUSED

def test_solana_swap_sender_cancel(backend, exchange_navigation_helper):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES)
    ex.check_transaction_signature(partner)

    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER):
        exchange_navigation_helper.simple_reject()
    assert ex.get_check_address_response().status == Errors.USER_REFUSED


# SOL callbacks refuse to validate exchange fields

def test_solana_swap_recipient_unowned_payout_address(backend):
    tampered_tx_infos = VALID_SWAP_ETH_TO_SOL_TX_INFOS.copy()
    tampered_tx_infos["payout_address"] = SOL.FOREIGN_ADDRESS

    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tampered_tx_infos, ETH_FEES)
    ex.check_transaction_signature(partner)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER):
        pass
    assert ex.get_check_address_response().status == Errors.INVALID_ADDRESS


def test_solana_swap_sender_unowned_refund_address(backend):
    tampered_tx_infos = VALID_SWAP_SOL_TO_ETH_TX_INFOS.copy()
    tampered_tx_infos["refund_address"] = SOL.FOREIGN_ADDRESS

    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tampered_tx_infos, SOL.FEES)
    ex.check_transaction_signature(partner)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER):
        pass
    assert ex.get_check_address_response().status == Errors.INVALID_ADDRESS


def test_solana_swap_recipient_payout_extra_id(backend):
    tampered_tx_infos = VALID_SWAP_ETH_TO_SOL_TX_INFOS.copy()
    tampered_tx_infos["payout_extra_id"] = "0xCAFE"

    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tampered_tx_infos, ETH_FEES)
    ex.check_transaction_signature(partner)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER):
        pass
    assert ex.get_check_address_response().status == Errors.INVALID_ADDRESS


def test_solana_swap_recipient_refund_extra_id(backend):
    tampered_tx_infos = VALID_SWAP_SOL_TO_ETH_TX_INFOS.copy()
    tampered_tx_infos["refund_extra_id"] = "0xCAFE"

    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tampered_tx_infos, SOL.FEES)
    ex.check_transaction_signature(partner)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER):
        pass
    assert ex.get_check_address_response().status == Errors.INVALID_ADDRESS


# Transaction validated in Exchange but Solana app receives a different message to sign

def test_solana_swap_sender_wrong_amount(backend, exchange_navigation_helper):
    valid_swap(backend, exchange_navigation_helper, VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT + 1)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(backend)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
        pass
    rapdu: RAPDU = sol.get_async_response()
    print("Received rapdu :", rapdu)
    assert rapdu.status == ErrorType.SOLANA_SUMMARY_FINALIZE_FAILED


def test_solana_swap_sender_wrong_destination(backend, exchange_navigation_helper):
    valid_swap(backend, exchange_navigation_helper, VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY_2, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(backend)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
        pass
    rapdu: RAPDU = sol.get_async_response()
    print("Received rapdu :", rapdu)
    assert rapdu.status == ErrorType.SOLANA_SUMMARY_FINALIZE_FAILED
