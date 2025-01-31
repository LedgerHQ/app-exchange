import pytest
import os

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES
from .apps import cal as cal
from .apps.aptos import AptosCommandSender

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
        print("----------------------perform_final_tx----------------------")
        if destination != self.valid_destination_1 or destination == self.valid_destination_2:
            assert False
        transaction = bytes.fromhex("b5e97db07fa0bd0e5598aa3643a9bc6f6693bddc1a9fec9e674a461eaa00b193094c6fc0d3b382a599c37e1aaa7618eff2c96a3586876082c4594c50c50d7dde1b000000000000000200000000000000000000000000000000000000000000000000000000000000010d6170746f735f6163636f756e74087472616e736665720002203835075df1bf469c336eabed8ac87052ee4485f3ec93380a5382fbf76b7a33070840420f000000000006000000000000006400000000000000c39aa4640000000002")
        AptosCommandSender(self.backend).sign_tx(path="m/44'/637'/0''",transaction=transaction)

# Use a class to reuse the same Speculos instance
class TestsAptos:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
    def test_aptos(self, backend, exchange_navigation_helper, test_to_run):
        AptosTests(backend, exchange_navigation_helper).run_test(test_to_run)
