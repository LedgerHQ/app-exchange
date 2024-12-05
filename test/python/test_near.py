import pytest

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_AND_FEES, ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES
from .apps.near import  NearClient, NearErrors
from .apps import cal as cal

# ExchangeTestRunner implementation for Near
class NearTests(ExchangeTestRunner):

    currency_configuration = cal.NEAR_CURRENCY_CONFIGURATION
    valid_destination_1 = "speculos.testnet"
    valid_destination_memo_1 = ""
    valid_destination_2 = "speculo.testnet"
    valid_destination_memo_2 = ""
    valid_refund = "EFr6nRvgKKeteKoEH7hudt8UHYiu94Liq2yMM7x2AU9U"
    valid_refund_memo = ""
    valid_send_amount_1 = 446739662
    valid_send_amount_2 = 1
    valid_fees_1 = 0
    valid_fees_2 = 0
    fake_refund = "abcdabcd"
    fake_refund_memo = "bla"
    fake_payout = "abcdabcd"
    fake_payout_memo = "bla"
    signature_refusal_error_code = NearErrors.SW_SWAP_CHECKING_FAIL

    def perform_final_tx(self, destination, send_amount, fees, memo):
        NearClient(self.backend).send_simple_sign_tx(path="m/44'/397'/0'/0'/1'",
                                                    destination=destination,
                                                    send_amount=send_amount)

        # TODO : assert signature validity


# Use a class to reuse the same Speculos instance
class TestsNear:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
    def test_near(self, backend, exchange_navigation_helper, test_to_run):
        NearTests(backend, exchange_navigation_helper).run_test(test_to_run)
