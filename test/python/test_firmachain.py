import pytest

from exchange_client.test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_THORSWAP
from apps.firmachain import FirmachainClient, Errors
from apps import cal as cal

class FirmachainTests(ExchangeTestRunner):
    currency_configuration = cal.FIRMACHAIN_CURRENCY_CONFIGURATION
    valid_destination_1 = "firma1w34k53py5v5xyluazqpq65agyajavep2d6hhtd"
    valid_destination_2 = "firma1hr9x0sjvel6z3vt9qny8sdd5gnnlgk0p5k9dfk"
    valid_refund = "firma12d64j98tjjpqkx70r08aspc4nvntqp2w5ataur"
    valid_send_amount_1 = 234567822222222
    valid_send_amount_2 = 2345678234234234
    valid_fees_1 = 173469283649234
    valid_fees_2 = 1762354526354
    fake_refund = "abcdabcd"
    fake_payout = "abcdabcd"
    valid_destination_memo_2 = "testmemo"
    wrong_method_error_code = Errors.ERR_SWAP_CHECK_WRONG_METHOD
    wrong_destination_error_code = Errors.ERR_SWAP_CHECK_WRONG_DEST_ADDR
    wrong_amount_error_code = Errors.ERR_SWAP_CHECK_WRONG_AMOUNT
    wrong_fees_error_code = Errors.ERR_SWAP_CHECK_WRONG_FEES
    wrong_memo_error_code = Errors.ERR_SWAP_CHECK_WRONG_MEMO

    def perform_final_tx(self, destination, send_amount, fees, memo):
        firmachain = FirmachainClient(self.backend)
        firmachain.perform_firmachain_transaction(destination, send_amount, fees, memo)

class TestsFirmachain:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_THORSWAP)
    def test_firmachain(self, backend, exchange_navigation_helper, test_to_run):
        FirmachainTests(backend, exchange_navigation_helper).run_test(test_to_run)
