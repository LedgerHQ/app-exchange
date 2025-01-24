import pytest
import os

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES
from .apps import cal as cal

# ExchangeTestRunner implementation for Ton
class AptosTests(ExchangeTestRunner):
    currency_configuration = cal.APTOS_CURRENCY_CONFIGURATION
    valid_destination_1 = "TNbtZSpknaQvC7jPCLU4znJMgm8fhuGTTY"
    valid_destination_memo_1 = ""
    valid_destination_2 = "TBoTZcARzWVgnNuB9SyE3S5g1RwsXoQL16"
    valid_destination_memo_2 = ""
    valid_refund = "0x8F13F355F3AF444BD356ADEAAAF01235A7817D6A4417F5C9FA3D74A68F7B7AFD"
    valid_refund_memo = ""
    valid_send_amount_1 = 1000000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 0
    valid_fees_2 = 1
    fake_refund = "abcdabcd"
    fake_refund_memo = "1"
    fake_payout = "abcdabcd"
    fake_payout_memo = "1"
    def perform_final_tx(self, destination, send_amount, fees, memo):
        assert False


# Use a class to reuse the same Speculos instance
class TestsAptos:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
    def test_aptos(self, backend, exchange_navigation_helper, test_to_run):
        AptosTests(backend, exchange_navigation_helper).run_test(test_to_run)


def test_eval():
    assert False