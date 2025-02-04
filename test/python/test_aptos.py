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
    valid_send_amount_1 = 42
    valid_send_amount_2 = 446739662
    valid_fees_1 = 0
    valid_fees_2 = 1
    fake_refund = "abcdabcd"
    fake_refund_memo = "1"
    fake_payout = "abcdabcd"
    fake_payout_memo = "1"
    def perform_final_tx(self, destination, send_amount, fees, memo):
        if destination == self.valid_destination_1:
            transaction = bytes.fromhex("b5e97db07fa0bd0e5598aa3643a9bc6f6693bddc1a9fec9e674a461eaa00b193783135e8b00430253a22ba041d860c373d7a1501ccf7ac2d1ad37a8ed2775aee000000000000000002000000000000000000000000000000000000000000000000000000000000000104636f696e087472616e73666572010700000000000000000000000000000000000000000000000000000000000000010a6170746f735f636f696e094170746f73436f696e000220544e62745a53706b6e61517643376a50434c55347a6e4a4d676d386668754700082a00000000000000204e0000000000006400000000000000565c51630000000022")
            AptosCommandSender(self.backend).sign_tx(transaction=transaction)
        if destination == self.valid_destination_2:
            transaction = bytes.fromhex("b5e97db07fa0bd0e5598aa3643a9bc6f6693bddc1a9fec9e674a461eaa00b193783135e8b00430253a22ba041d860c373d7a1501ccf7ac2d1ad37a8ed2775aee000000000000000002000000000000000000000000000000000000000000000000000000000000000104636f696e087472616e73666572010700000000000000000000000000000000000000000000000000000000000000010a6170746f735f636f696e094170746f73436f696e00022054426F545A6341527A5756676E4E7542395379453353356731527773586F510008ceb4a01a00000000204e0000000000006400000000000000565c51630000000022")
            AptosCommandSender(self.backend).sign_tx(transaction=transaction)
            

# Use a class to reuse the same Speculos instance
class TestsAptos:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
    def test_aptos(self, backend, exchange_navigation_helper, test_to_run):
        AptosTests(backend, exchange_navigation_helper).run_test(test_to_run)
