import pytest
from hashlib import blake2b

from .apps.exchange_test_runner import ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP, ExchangeTestRunner
from .apps.sui import SuiClient, ErrorType
from .apps import cal as cal
from .apps import sui_utils as SUI
from .apps.sui_utils import verify_signature

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
    signature_refusal_error_code = ErrorType.SUI_USER_CANCELLED[0]

    partner_name = "Partner name"
    fund_user_id = "Daft Punk"
    fund_account_name = "Account 0"

    def perform_final_tx(self, destination, send_amount, fees, _memo):
        sui = SuiClient(self.backend, verbose=False)
        tx = sui.build_simple_transaction(SUI.OWNED_ADDRESS, destination, send_amount, fees)
        signature = sui.sign_transaction(SUI.SUI_PACKED_DERIVATION_PATH, tx)

        public_key_bytes = bytes.fromhex(SUI.OWNED_PUBLIC_KEY[2:])
        verify_signature(public_key_bytes, blake2b(tx, digest_size=32).digest(), signature)

class TestsSui:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP)
    def test_sui(self, backend, exchange_navigation_helper, test_to_run):
        GenericSuiTests(backend, exchange_navigation_helper).run_test(test_to_run)
