import pytest
import base58

from ragger.bip import pack_derivation_path
from ragger.backend import BackendInterface
from ragger.firmware import Firmware

from ledger_app_clients.exchange.test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP
from ledger_app_clients.exchange.navigation_helper import ExchangeNavigationHelper
from .apps.cardano import CardanoClient, Errors
from .apps.cardano import ADA_BYRON_DERIVATION_PATH, ADA_SHELLEY_DERIVATION_PATH
from .apps import cal as cal


# ExchangeTestRunner implementation for Cardano
# class CardanoByronClientTests(ExchangeTestRunner):

#     # Addresses Generated on MainNet
#     currency_configuration = cal.ADA_BYRON_CURRENCY_CONFIGURATION
#     valid_destination_1 = "Ae2tdPwUPEZ7X4rA8Z34X1QGJq4LBcaKPKzWFB5rfEUUWVDANKNZZLT9Ass" # path "m/44'/1815'/1'/0/0"
#     valid_destination_2 = "Ae2tdPwUPEZF1dUU2kCn3yhqNqPMEuoLwwJPPTHjeZco2SMyGNS351ykBqX" # path "m/44'/1815'/2'/0/0"
#     valid_refund = "Ae2tdPwUPEZEvjAYDYFfaJ4ZDELKcyxLQUwxADi5V8gmzBjvxtt3LqZxgSq" # path "m/44'/1815'/0'/0/0"
#     valid_send_amount_1 = 3003112
#     valid_send_amount_2 = 446739662
#     valid_fees_1 = 42
#     valid_fees_2 = 28
#     fake_refund = "abcdabcd"
#     fake_payout = "abcdabcd"
#     signature_refusal_error_code = Errors.SW_SWAP_CHECKING_FAIL

#     def perform_final_tx(self, destination: str, send_amount: int, fees: int, memo) -> None:
#         CardanoClient(self.backend).perform_byron_sign_tx(ADA_BYRON_DERIVATION_PATH,
#                                                           base58.b58decode(destination).hex(),
#                                                           f"{send_amount:016x}",
#                                                           f"{fees:016x}")


SHELLEY_DESTINATION = {
    "valid_1": {
        "addr": "addr1q80r70qggedqy90z4rzy6kynv4xqejxfxqmangwhz8ugalfwlqyt4mswmh4hl0nnq53r4rp798vj4c7p7f2wdgqnc8uqt2xltv",
        "path": "01de3f3c08465a0215e2a8c44d5893654c0cc8c93037d9a1d711f88efd2ef808baee0eddeb7fbe7305223a8c3e29d92ae3c1f254e6a013c1f8"},
    "valid_2": {
        "addr": "addr1q84sh2j72ux0l03fxndjnhctdg7hcppsaejafsa84vh7lwgmcs5wgus8qt4atk45lvt4xfxpjtwfhdmvchdf2m3u3hlsd5tq5r",
        "path": "01eb0baa5e570cffbe2934db29df0b6a3d7c0430ee65d4c3a7ab2fefb91bc428e4720702ebd5dab4fb175324c192dc9bb76cc5da956e3c8dff"},
}

# ExchangeTestRunner implementation for Cardano
class CardanoShelleyClientTests(ExchangeTestRunner):

    # Addresses Generated on MainNet, type BASE_PAYMENT_KEY_STAKE_KEY
    currency_configuration = cal.ADA_SHELLEY_CURRENCY_CONFIGURATION
    valid_destination_1 = SHELLEY_DESTINATION["valid_1"]["addr"]
    valid_destination_2 = SHELLEY_DESTINATION["valid_2"]["addr"]
    # Refund address corresponds to the derivation path "m/1852'/1815'/0'/0/0" and "m/1852'/1815'/0'/2/0"
    valid_refund = "addr1q9kl5z2zd9vakyprvw0g68c8hv0y0rnj93htc82hh2rs8wwmyx0wtn56wnuclkku9hsnal8dtg25a7x56svjn4dlnlmq7quz6p"
    valid_send_amount_1 = 4671693
    valid_send_amount_2 = 446739662
    valid_fees_1 = 174345
    valid_fees_2 = 28
    fake_refund = "abcdabcd"
    fake_payout = "abcdabcd"
    signature_refusal_error_code = Errors.SW_SWAP_CHECKING_FAIL

    def perform_final_tx(self, destination: str, send_amount: int, fees: int, memo) -> None:
        # Create a reverse lookup dictionary
        addr_to_path = {v["addr"]: v["path"] for v in SHELLEY_DESTINATION.values()}
        CardanoClient(self.backend).perform_shelley_sign_tx(addr_to_path.get(destination),
                                                            f"{send_amount:016x}",
                                                            f"{fees:016x}")


# Use a class to reuse the same Speculos instance
class TestsCardanoClient:

    # Test Ready, but legacy and unused address format
    # @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP)
    # def test_cardano_byron(self, 
    #                        backend: BackendInterface,
    #                        exchange_navigation_helper: ExchangeNavigationHelper,
    #                        test_to_run: str) -> None:
    #     if backend.firmware == Firmware.NANOS:
    #         pytest.skip("Cardano swap is not supported on NanoS device")
    #     CardanoByronClientTests(backend, exchange_navigation_helper).run_test(test_to_run)

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP)
    def test_cardano_shelley(self,
                             backend: BackendInterface,
                             exchange_navigation_helper: ExchangeNavigationHelper,
                             test_to_run: str) -> None:
        if backend.firmware == Firmware.NANOS:
            pytest.skip("Cardano swap is not supported on NanoS device")
        CardanoShelleyClientTests(backend, exchange_navigation_helper).run_test(test_to_run)
