from time import sleep
import pytest

from ragger.backend import RaisePolicy
from ragger.utils import pack_APDU, RAPDU
from ragger.error import ExceptionRAPDU

from .apps.exchange import ExchangeClient, Rate, SubCommand, ERRORS
from .apps.ethereum import EthereumClient, ERR_SILENT_MODE_CHECK_FAILED, eth_amount_to_wei_hex_string

from .apps.solana import SolanaClient, ErrorType
from .apps.solana_utils import SOL_PACKED_DERIVATION_PATH
from .apps.solana_cmd_builder import SystemInstructionTransfer, Message, verify_signature
from .apps import solana_utils as SOL

from .signing_authority import SigningAuthority, LEDGER_SIGNER

ETH_AMOUNT = eth_amount_to_wei_hex_string(0.09000564)
ETH_FEES = eth_amount_to_wei_hex_string(0.000588)

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
def valid_swap(client, firmware, tx_infos, fees, right_clicks):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tx_infos, fees)
    ex.check_transaction_signature(partner)
    ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER, right_clicks=right_clicks)
    ex.start_signing_transaction()
    sleep(0.1)


# Validate regular ETH <-> SOL exchanges

def test_solana_swap_recipient_ok(client, firmware):
    valid_swap(client, firmware, VALID_SWAP_ETH_TO_SOL_TX_INFOS, bytes.fromhex(ETH_FEES), right_clicks = 4)

    eth = EthereumClient(client, derivation_path=bytes.fromhex("058000002c8000003c800000000000000000000000"))
    eth.get_public_key()
    eth.sign(extra_payload=bytes.fromhex("ec09850684ee180082520894d692cb1346262f584d17b4b470954501f6715a8288" + ETH_AMOUNT + "80018080"))

def test_solana_swap_sender_ok(client, firmware):
    valid_swap(client, firmware, VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES_BYTES, right_clicks = 4)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(client)
    signature: bytes = sol.send_blind_sign_message(SOL_PACKED_DERIVATION_PATH, message).data
    verify_signature(SOL.OWNED_PUBLIC_KEY, message, signature)

def test_solana_swap_sender_double_sign(client, firmware):
    valid_swap(client, firmware, VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES_BYTES, right_clicks = 4)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(client)
    signature: bytes = sol.send_blind_sign_message(SOL_PACKED_DERIVATION_PATH, message).data
    verify_signature(SOL.OWNED_PUBLIC_KEY, message, signature)

    with pytest.raises(Exception) as e_info:
        # App should have quit
        sol.send_blind_sign_message(SOL_PACKED_DERIVATION_PATH, message)

# Validate canceled ETH <-> SOL exchanges

def test_solana_swap_recipient_cancel(client, firmware):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(VALID_SWAP_ETH_TO_SOL_TX_INFOS, bytes.fromhex(ETH_FEES))
    ex.check_transaction_signature(partner)

    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER, right_clicks=5, accept=False)
    print("Received rapdu :", rapdu)
    assert rapdu.status == ERRORS["USER_REFUSED"].status

def test_solana_swap_sender_cancel(client, firmware):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES_BYTES)
    ex.check_transaction_signature(partner)

    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER, right_clicks=5, accept=False)
    print("Received rapdu :", rapdu)
    assert rapdu.status == ERRORS["USER_REFUSED"].status


# SOL callbacks refuse to validate exchange fields

def test_solana_swap_recipient_unowned_payout_address(client, firmware):
    tampered_tx_infos = VALID_SWAP_ETH_TO_SOL_TX_INFOS.copy()
    tampered_tx_infos["payout_address"] = SOL.FOREIGN_ADDRESS

    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tampered_tx_infos, bytes.fromhex(ETH_FEES))
    ex.check_transaction_signature(partner)
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER)
    assert rapdu.status == ERRORS["INVALID_ADDRESS"].status


def test_solana_swap_sender_unowned_refund_address(client, firmware):
    tampered_tx_infos = VALID_SWAP_SOL_TO_ETH_TX_INFOS.copy()
    tampered_tx_infos["refund_address"] = SOL.FOREIGN_ADDRESS

    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tampered_tx_infos, SOL.FEES_BYTES)
    ex.check_transaction_signature(partner)
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER)
    assert rapdu.status == ERRORS["INVALID_ADDRESS"].status


def test_solana_swap_recipient_payout_extra_id(client, firmware):
    tampered_tx_infos = VALID_SWAP_ETH_TO_SOL_TX_INFOS.copy()
    tampered_tx_infos["payout_extra_id"] = "0xCAFE"

    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tampered_tx_infos, bytes.fromhex(ETH_FEES))
    ex.check_transaction_signature(partner)
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER)
    assert rapdu.status == ERRORS["INVALID_ADDRESS"].status


def test_solana_swap_recipient_refund_extra_id(client, firmware):
    tampered_tx_infos = VALID_SWAP_SOL_TO_ETH_TX_INFOS.copy()
    tampered_tx_infos["refund_extra_id"] = "0xCAFE"

    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tampered_tx_infos, SOL.FEES_BYTES)
    ex.check_transaction_signature(partner)
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = ex.check_address(LEDGER_SIGNER, LEDGER_SIGNER)
    assert rapdu.status == ERRORS["INVALID_ADDRESS"].status


# Transaction validated in Exchange but Solana app receives a different message to sign

def test_solana_swap_sender_wrong_amount(client, firmware):
    valid_swap(client, firmware, VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES_BYTES, right_clicks = 4)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT + 1)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(client)
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = sol.send_blind_sign_message(SOL_PACKED_DERIVATION_PATH, message)
    print("Received rapdu :", rapdu)
    assert rapdu.status == ErrorType.USER_CANCEL


def test_solana_swap_sender_wrong_destination(client, firmware):
    valid_swap(client, firmware, VALID_SWAP_SOL_TO_ETH_TX_INFOS, SOL.FEES_BYTES, right_clicks = 4)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY_2, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(client)
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = sol.send_blind_sign_message(SOL_PACKED_DERIVATION_PATH, message)
    print("Received rapdu :", rapdu)
    assert rapdu.status == ErrorType.USER_CANCEL
