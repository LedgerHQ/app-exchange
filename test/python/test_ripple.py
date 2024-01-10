import pytest

from .apps.exchange_test_runner import ExchangeTestRunner, SWAP_TESTS
from .apps.xrp import XRPClient, DEFAULT_PATH, XRP_PACKED_DERIVATION_PATH, RippleErrors

# ExchangeTestRunner implementation for Stellar
class RippleTests(ExchangeTestRunner):
    currency_ticker = "XRP"
    valid_destination_1 = "ra7Zr8ddy9tB88RaXL8B87YkqhEJG2vkAJ"
    valid_destination_memo_1 = "0"
    valid_destination_2 = "rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4"
    valid_destination_memo_2 = "123"
    valid_refund = "ra7Zr8ddy9tB88RaXL8B87YkqhEJG2vkAJ"
    valid_refund_memo = ""
    valid_send_amount_1 = 1000000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100
    valid_fees_2 = 10078
    fake_refund = "abcdabcd"
    fake_refund_memo = ""
    fake_payout = "abcdabcd"
    fake_payout_memo = ""
    signature_refusal_error_code = RippleErrors.SW_SWAP_CHECKING_FAIL

    def perform_final_tx(self, destination, send_amount, fees, memo):
        XRPClient(self.backend).send_simple_sign_tx(path="m/44'/144'/0'/0'/0",
                                                    fees=fees,
                                                    memo=memo,
                                                    destination=destination,
                                                    send_amount=send_amount)

        # TODO : assert signature validity


# Use a class to reuse the same Speculos instance
class TestsRipple:

    @pytest.mark.parametrize('test_to_run', SWAP_TESTS)
    def test_ripple(self, backend, exchange_navigation_helper, test_to_run):
        RippleTests(backend, exchange_navigation_helper).run_test(test_to_run)
