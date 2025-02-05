import pytest

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES, VALID_TESTS_EXCEPT_THORSWAP, ALL_TESTS_EXCEPT_THORSWAP
from .apps.cosmos import CosmosClient, Errors
from .apps import cal as cal

# ExchangeTestRunner implementation for Cosmos
class CosmosTests(ExchangeTestRunner):
    currency_configuration = cal.COSMOS_CURRENCY_CONFIGURATION
    valid_destination_1 = "cosmos1wkd9tfm5pqvhhaxq77wv9tvjcsazuaykwsld65"
    valid_destination_2 = "cosmos14lultfckehtszvzw4ehu0apvsr77afvyhgqhwh"
    valid_refund = "cosmos1xma4fjm0lm4y6j3f82hzzwycjas5dkcn7pzjlk"
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
        cosmos = CosmosClient(self.backend)
        cosmos.perform_cosmos_transaction(destination, send_amount, fees, memo)

# Use a class to reuse the same Speculos instance
class TestsCosmos:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_THORSWAP)
    def test_cosmos(self, backend, exchange_navigation_helper, test_to_run):
        if backend.firmware.device == "nanos":
            pytest.skip("Cosmos swap is not supported on NanoS device")
        CosmosTests(backend, exchange_navigation_helper).run_test(test_to_run)
