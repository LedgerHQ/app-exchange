import pytest

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES
from .apps.polkadot import PolkadotClient, Errors
from .apps import cal as cal

# ExchangeTestRunner implementation for Polkadot
class PolkadotTests(ExchangeTestRunner):
    currency_configuration = cal.DOT_CURRENCY_CONFIGURATION
    valid_destination_1 = "15ED4RbHLbz5zYhdij9yyEjKZZjuUC6CdxKZ14f4aKSkjL9H"
    valid_destination_2 = "13zAiMiN2HdJfEXn4NkVCWxuemScdaXGYKJrbJr1Nt6kjBRD"
    valid_refund = "14TwSqXEoCPK7Q7Jnk2RFzbPZXppsxz24bHaQ7fakwio7DFn"
    valid_send_amount_1 = 125138026362100973352314721007221280020
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100000000
    valid_fees_2 = 10000123
    fake_refund = "abcdabcd"
    fake_payout = "abcdabcd"
    wrong_method_error_code = Errors.ERR_SWAP_CHECK_WRONG_METHOD
    wrong_destination_error_code = Errors.ERR_SWAP_CHECK_WRONG_DEST_ADDR
    wrong_amount_error_code = Errors.ERR_SWAP_CHECK_WRONG_AMOUNT

    def perform_final_tx(self, destination, send_amount, fees, memo):
        dot = PolkadotClient(self.backend)
        dot.perform_polkadot_transaction(destination, send_amount)

# Use a class to reuse the same Speculos instance
class TestsPolkadot:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
    def test_polkadot(self, backend, exchange_navigation_helper, test_to_run):
        pytest.skip("Polkadot swap test is disabled")

        # if backend.firmware.device == "nanos":
        #     pytest.skip("Polkadot swap is not supported on NanoS device")
        # PolkadotTests(backend, exchange_navigation_helper).run_test(test_to_run)
