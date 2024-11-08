import pytest
import base58

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP
from .apps.cardano import CardanoClient, Errors
from .apps.cardano import ADA_BYRON_DERIVATION_PATH
from .apps import cal as cal


# ExchangeTestRunner implementation for Cardano
class CardanoByronClientTests(ExchangeTestRunner):

    # Addresses Generated on MainNet
    currency_configuration = cal.ADA_BYRON_CURRENCY_CONFIGURATION
    valid_destination_1 = "Ae2tdPwUPEZ7X4rA8Z34X1QGJq4LBcaKPKzWFB5rfEUUWVDANKNZZLT9Ass" # path "m/44'/1815'/1'/0/0"
    valid_destination_2 = "Ae2tdPwUPEZF1dUU2kCn3yhqNqPMEuoLwwJPPTHjeZco2SMyGNS351ykBqX" # path "m/44'/1815'/2'/0/0"
    valid_refund = "Ae2tdPwUPEZEvjAYDYFfaJ4ZDELKcyxLQUwxADi5V8gmzBjvxtt3LqZxgSq" # path "m/44'/1815'/0'/0/0"
    valid_send_amount_1 = 3003112
    valid_send_amount_2 = 446739662
    valid_fees_1 = 42
    valid_fees_2 = 28
    fake_refund = "abcdabcd"
    fake_payout = "abcdabcd"
    signature_refusal_error_code = Errors.SW_SWAP_CHECKING_FAIL

    def perform_final_tx(self, destination: str, send_amount: int, fees: int, memo) -> None:
        CardanoClient(self.backend).perform_byron_sign_tx(ADA_BYRON_DERIVATION_PATH,
                                                          base58.b58decode(destination).hex(),
                                                          f"{send_amount:016x}",
                                                          f"{fees:016x}")


# Use a class to reuse the same Speculos instance
class TestsCardanoClient:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP)
    def test_cardano(self, backend, exchange_navigation_helper, test_to_run):
        CardanoByronClientTests(backend, exchange_navigation_helper).run_test(test_to_run)