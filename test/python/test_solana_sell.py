from .apps.exchange import ExchangeClient, Rate, SubCommand, ERRORS
from .apps.ethereum import EthereumClient

from .apps.solana import SolanaClient, ErrorType
from .apps.solana_utils import SOL_PACKED_DERIVATION_PATH
from .apps.solana_cmd_builder import SystemInstructionTransfer, Message, verify_signature
from .apps import solana_utils as SOL

from ragger.backend.interface import RAPDU, RaisePolicy

from .signing_authority import SigningAuthority, LEDGER_SIGNER


# Sell transaction infos for valid SOL SELL. Tamper the values to generate errors
VALID_SELL_SOL_TX_INFOS = {
    "trader_email": "john@doe.lost",
    "out_currency": "USD",
    "out_amount": {"coefficient": b"\x01", "exponent": 3},
    "in_currency": "SOL",
    "in_amount": SOL.AMOUNT_BYTES,
    "in_address": SOL.FOREIGN_ADDRESS
}

# Helper to validate a SELL transaction by the Exchange app and put the Solana app in front
def valid_sell(client, firmware, tx_infos, fees, right_clicks):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SELL)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(tx_infos, fees)
    ex.check_transaction_signature(partner)
    ex.check_address(LEDGER_SIGNER, right_clicks=right_clicks)
    ex.start_signing_transaction()


def test_solana_sell_ok(client, firmware):
    valid_sell(client, firmware, VALID_SELL_SOL_TX_INFOS, SOL.FEES_BYTES, right_clicks=5)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(client)
    signature: bytes = sol.send_blind_sign_message(SOL_PACKED_DERIVATION_PATH, message).data
    verify_signature(SOL.OWNED_PUBLIC_KEY, message, signature)


def test_solana_sell_wrong_amount(client, firmware):
    valid_sell(client, firmware, VALID_SELL_SOL_TX_INFOS, SOL.FEES_BYTES, right_clicks=5)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT + 1)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(client)
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = sol.send_blind_sign_message(SOL_PACKED_DERIVATION_PATH, message)
    print("Received rapdu :", rapdu)
    assert rapdu.status == ErrorType.USER_CANCEL


def test_solana_sell_wrong_destination(client, firmware):
    valid_sell(client, firmware, VALID_SELL_SOL_TX_INFOS, SOL.FEES_BYTES, right_clicks=5)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY_2, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(client)
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = sol.send_blind_sign_message(SOL_PACKED_DERIVATION_PATH, message)
    print("Received rapdu :", rapdu)
    assert rapdu.status == ErrorType.USER_CANCEL


def test_solana_sell_cancel(client, firmware):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SELL)
    partner = SigningAuthority(curve=ex.partner_curve, name="Partner name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    ex.process_transaction(VALID_SELL_SOL_TX_INFOS, SOL.FEES_BYTES)
    ex.check_transaction_signature(partner)

    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.check_address(LEDGER_SIGNER, right_clicks=5, accept=False)
    print("Received rapdu :", rapdu)
    assert rapdu.status == ERRORS["USER_REFUSED"].status
