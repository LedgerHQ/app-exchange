from ragger.backend.interface import RAPDU, RaisePolicy

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors
from .apps.ethereum import EthereumClient

from .apps.solana import SolanaClient, ErrorType
from .apps.solana_utils import SOL_PACKED_DERIVATION_PATH
from .apps.solana_cmd_builder import SystemInstructionTransfer, Message, verify_signature
from .apps import solana_utils as SOL

from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps.exchange_transaction_builder import get_partner_curve, craft_tx, encode_tx, extract_payout_ticker, extract_refund_ticker
from .apps import cal as cal


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
def valid_sell(backend, exchange_navigation_helper, tx_infos, fees):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SELL)
    partner = SigningAuthority(curve=get_partner_curve(SubCommand.FUND), name="Partner name")

    transaction_id = ex.init_transaction().data
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    tx = craft_tx(SubCommand.SELL, tx_infos, transaction_id)
    ex.process_transaction(tx, fees)
    encoded_tx = encode_tx(SubCommand.SELL, partner, tx)
    ex.check_transaction_signature(encoded_tx)

    payout_ticker = extract_payout_ticker(SubCommand.SELL, tx_infos)
    with ex.check_address(cal.get_conf_for_ticker(payout_ticker)):
        exchange_navigation_helper.simple_accept()
    ex.start_signing_transaction()


def test_solana_sell_ok(backend, exchange_navigation_helper):
    valid_sell(backend, exchange_navigation_helper, VALID_SELL_SOL_TX_INFOS, SOL.FEES)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(backend)
    with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
        # Instant rapdu expected
        pass
    signature: bytes = sol.get_async_response().data
    verify_signature(SOL.OWNED_PUBLIC_KEY, message, signature)


def test_solana_sell_wrong_amount(backend, exchange_navigation_helper):
    valid_sell(backend, exchange_navigation_helper, VALID_SELL_SOL_TX_INFOS, SOL.FEES)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY, SOL.AMOUNT + 1)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(backend)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
        # Instant rapdu expected
        pass
    rapdu: RAPDU = sol.get_async_response()
    print("Received rapdu :", rapdu)
    assert rapdu.status == ErrorType.SOLANA_SUMMARY_FINALIZE_FAILED


def test_solana_sell_wrong_destination(backend, exchange_navigation_helper):
    valid_sell(backend, exchange_navigation_helper, VALID_SELL_SOL_TX_INFOS, SOL.FEES)

    instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, SOL.FOREIGN_PUBLIC_KEY_2, SOL.AMOUNT)
    message: bytes = Message([instruction]).serialize()

    sol = SolanaClient(backend)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
        # Instant rapdu expected
        pass
    rapdu: RAPDU = sol.get_async_response()
    print("Received rapdu :", rapdu)
    assert rapdu.status == ErrorType.SOLANA_SUMMARY_FINALIZE_FAILED


def test_solana_sell_cancel(backend, exchange_navigation_helper):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SELL)
    partner = SigningAuthority(curve=get_partner_curve(SubCommand.FUND), name="Partner name")

    transaction_id = ex.init_transaction().data
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
    tx = craft_tx(SubCommand.SELL, VALID_SELL_SOL_TX_INFOS, transaction_id)
    ex.process_transaction(tx, SOL.FEES)
    encoded_tx = encode_tx(SubCommand.SELL, partner, tx)
    ex.check_transaction_signature(encoded_tx)
    payout_ticker = extract_payout_ticker(SubCommand.SELL, VALID_SELL_SOL_TX_INFOS)

    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(cal.get_conf_for_ticker(payout_ticker)):
        exchange_navigation_helper.simple_reject()
    assert ex.get_check_address_response().status == Errors.USER_REFUSED
