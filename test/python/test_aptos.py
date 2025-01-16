import pytest
import os
from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES
from .apps.aptos import APTOS_DERIVATION_PATH
from .apps import cal as cal

# ExchangeTestRunner implementation for Ton
class AptosTests(ExchangeTestRunner):

    def perform_final_tx(self, destination, send_amount, fees, memo):
        assert False


# Use a class to reuse the same Speculos instance
class TestsAptos:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
    def test_aptos(self, backend, exchange_navigation_helper, test_to_run):
        AptosTests(backend, exchange_navigation_helper).run_test(test_to_run)


def test_eval():
    assert False