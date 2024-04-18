import pytest

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_AND_FEES
from .apps.polkadot import PolkadotClient, ERR_SWAP_CHECK_WRONG_METHOD, ERR_SWAP_CHECK_WRONG_DEST_ADDR, ERR_SWAP_CHECK_WRONG_AMOUNT
from .apps import cal as cal

# ExchangeTestRunner implementation for Polkadot
class PolkadotTests(ExchangeTestRunner):
    currency_configuration = cal.DOT_CURRENCY_CONFIGURATION
    valid_destination_1 = "14ypt3a2m9yiq4ZQDcJFrkD99C3ZoUjLCDz1gBpCDwJPqVDY"
    valid_destination_memo_1 = ""
    valid_destination_2 = "13zAiMiN2HdJfEXn4NkVCWxuemScdaXGYKJrbJr1Nt6kjBRD"
    valid_destination_memo_2 = ""
    valid_refund = "14TwSqXEoCPK7Q7Jnk2RFzbPZXppsxz24bHaQ7fakwio7DFn"
    valid_refund_memo = ""
    valid_send_amount_1 = 12345670000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100000000
    valid_fees_2 = 10000123
    fake_refund = "abcdabcd"
    fake_refund_memo = ""
    fake_payout = "abcdabcd"
    fake_payout_memo = ""
    wrong_method_error_code = ERR_SWAP_CHECK_WRONG_METHOD
    wrong_destination_error_code = ERR_SWAP_CHECK_WRONG_DEST_ADDR
    wrong_amount_error_code = ERR_SWAP_CHECK_WRONG_AMOUNT

    def perform_final_tx(self, destination, send_amount, fees, memo):
        dot = PolkadotClient(self.backend)
        # Get public key.
        key = dot.get_pubkey()
        # Init signature process and assert response APDU code is 0x9000 (OK).
        dot.sign_init().status
        # craft tx
        message = PolkadotClient.craft_valid_polkadot_transaction(destination, send_amount, None, None)
        # Send message to be signed
        sign_response = dot.sign_last(message)

        # Assert signature is verified properly with key and message
        assert dot.verify_signature(hex_key=key,signature=sign_response.data[1:],message=message.hex().encode()) == True


# Use a class to reuse the same Speculos instance
class TestsPolkadot:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_AND_FEES)
    def test_polkadot(self, backend, exchange_navigation_helper, test_to_run):
        PolkadotTests(backend, exchange_navigation_helper).run_test(test_to_run)
