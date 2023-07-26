import pytest

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_AND_FEES
from .apps.solana import SolanaClient, ErrorType
from .apps.solana_utils import SOL_PACKED_DERIVATION_PATH
from .apps.solana_cmd_builder import SystemInstructionTransfer, Message, verify_signature
from .apps import solana_utils as SOL

# A bit hacky but way less hassle than actually writing an actual address decoder
SOLANA_ADDRESS_DECODER = {
    SOL.FOREIGN_ADDRESS: SOL.FOREIGN_PUBLIC_KEY,
    SOL.FOREIGN_ADDRESS_2: SOL.FOREIGN_PUBLIC_KEY_2,
}

# ExchangeTestRunner implementation for Stellar
class SolanaTests(ExchangeTestRunner):
    currency_ticker = "SOL"
    valid_destination_1 = SOL.FOREIGN_ADDRESS
    valid_destination_memo_1 = ""
    valid_destination_2 = SOL.FOREIGN_ADDRESS_2
    valid_destination_memo_2 = ""
    valid_refund = SOL.OWNED_ADDRESS
    valid_refund_memo = ""
    valid_send_amount_1 = SOL.AMOUNT
    valid_send_amount_2 = SOL.AMOUNT_2
    valid_fees_1 = SOL.FEES
    valid_fees_2 = SOL.FEES_2
    fake_refund = SOL.FOREIGN_ADDRESS
    fake_refund_memo = ""
    fake_payout = SOL.FOREIGN_ADDRESS
    fake_payout_memo = ""
    signature_refusal_error_code = ErrorType.SOLANA_SUMMARY_FINALIZE_FAILED

    partner_name = "Partner name"
    fund_user_id = "Daft Punk"
    fund_account_name = "Account 0"

    def perform_final_tx(self, destination, send_amount, fees, memo):
        decoded_destination = SOLANA_ADDRESS_DECODER[destination]
        instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, decoded_destination, send_amount)
        message: bytes = Message([instruction]).serialize()
        sol = SolanaClient(self.backend)
        with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
            pass
        signature: bytes = sol.get_async_response().data
        verify_signature(SOL.OWNED_PUBLIC_KEY, message, signature)


# Use a class to reuse the same Speculos instance
@pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_AND_FEES)
def test_solana(backend, exchange_navigation_helper, test_to_run):
    SolanaTests(backend, exchange_navigation_helper).run_test(test_to_run)
