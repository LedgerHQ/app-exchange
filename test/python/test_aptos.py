import pytest

from ledger_app_clients.exchange.test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP
from .apps import cal as cal
from .apps.aptos import AptosCommandSender, Errors

# ExchangeTestRunner implementation for Aptos
class AptosTests(ExchangeTestRunner):
    max_gas_amount = 100
    currency_configuration = cal.APTOS_CURRENCY_CONFIGURATION
    valid_destination_1 = "0x8F13f355F3aF444BD356ADEAAAF01235A7817D6A4417F5c9FA3D74A68F7b7AFD"
    valid_destination_memo_1 = ""
    valid_destination_2 = "0x7be51d04d3a482fa056bc094bc5eadad005aaf823a95269410f08730f0d03cb4"
    valid_destination_memo_2 = ""
    valid_refund = "0x8F13f355F3aF444BD356ADEAAAF01235A7817D6A4417F5c9FA3D74A68F7b7AFD"
    valid_refund_memo = ""
    valid_send_amount_1 = 42
    valid_send_amount_2 = 446739662
    valid_fees_1 = 6 * max_gas_amount
    valid_fees_2 = 42 * max_gas_amount
    fake_refund = "abcdabcd"
    fake_refund_memo = "1"
    fake_payout = "0x7be51d04d3a482fa056bc094bc5eadad005aaf823a95269410f08730f0d03cb47be51d04d3a482fa056bc094bc5eadad005aaf823a95269410f7be51d04d3a482fa056bc094bceadad00"
    fake_payout_memo = "1"
    signature_refusal_error_code = Errors.SW_SWAP_CHECKING_FAIL
    wrong_method_error_code = Errors.SW_SWAP_CHECKING_FAIL
    wrong_destination_error_code = Errors.SW_SWAP_CHECKING_FAIL
    wrong_amount_error_code = Errors.SW_SWAP_CHECKING_FAIL
    def perform_final_tx(self, destination, send_amount, fees, memo):
        AptosCommandSender(self.backend).sign_tx(send_amount=send_amount,fees=fees, max_gas_amount=self.max_gas_amount, transmitter=self.valid_refund,destination=destination)


# Use a class to reuse the same Speculos instance
class TestsAptos:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP)
    def test_aptos(self, backend, exchange_navigation_helper, test_to_run):
        AptosTests(backend, exchange_navigation_helper).run_test(test_to_run)
