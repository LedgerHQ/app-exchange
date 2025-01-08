import pytest

from .apps.exchange_test_runner import ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES, ExchangeTestRunner, SWAP_TESTS, MY_SWAP_TESTS
from .apps.sui import SuiClient, ErrorType
from .apps import cal as cal
from .apps import sui_utils as SUI

# ExchangeTestRunner implementation for Sui
class GenericSuiTests(ExchangeTestRunner):
    currency_configuration = cal.SUI_CURRENCY_CONFIGURATION
    valid_destination_1 = SUI.FOREIGN_ADDRESS
    valid_destination_2 = SUI.FOREIGN_ADDRESS_2
    valid_refund = SUI.OWNED_ADDRESS
    valid_send_amount_1 = SUI.AMOUNT
    valid_send_amount_2 = SUI.AMOUNT_2
    valid_fees_1 = SUI.FEES
    valid_fees_2 = SUI.FEES_2
    fake_refund = SUI.FOREIGN_ADDRESS
    fake_payout = SUI.FOREIGN_ADDRESS
    signature_refusal_error_code = 0x6E04

    partner_name = "Partner name"
    fund_user_id = "Daft Punk"
    fund_account_name = "Account 0"

    def perform_final_tx(self, destination, send_amount, _fees, _memo):
        sui = SuiClient(self.backend)
        tx = sui.build_simple_transaction(SUI.OWNED_ADDRESS, destination, send_amount)
        _signature = sui.sign_transaction(SUI.SUI_PACKED_DERIVATION_PATH, tx)

        #decoded_destination = SOLANA_ADDRESS_DECODER[destination]
        #instruction: SystemInstructionTransfer = SystemInstructionTransfer(SOL.OWNED_PUBLIC_KEY, decoded_destination, send_amount)
        #message: bytes = Message([instruction]).serialize()
        #sol = SolanaClient(self.backend)
        #with sol.send_async_sign_message(SOL_PACKED_DERIVATION_PATH, message):
        #    pass
        #signature: bytes = sol.get_async_response().data
        #verify_signature(SOL.OWNED_PUBLIC_KEY, message, signature)

# run with : ./test/python/ --golden_run --tb=short -v --device nanox -k sui  -W ignore::DeprecationWarning
class TestsSui:
    #@pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
    @pytest.mark.parametrize('test_to_run', MY_SWAP_TESTS)
    def test_sui(self, backend, exchange_navigation_helper, test_to_run):
        GenericSuiTests(backend, exchange_navigation_helper).run_test(test_to_run)
