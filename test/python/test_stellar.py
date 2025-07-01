import pytest

from ledger_app_clients.exchange.test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_THORSWAP
from .apps.stellar import Network, StellarClient, StellarErrors
from .apps import cal as cal

# ExchangeTestRunner implementation for Stellar
class StellarTests(ExchangeTestRunner):
    currency_configuration = cal.XLM_CURRENCY_CONFIGURATION
    valid_destination_1 = "GCKUD4BHIYSAYHU7HBB5FDSW6CSYH3GSOUBPWD2KE7KNBERP4BSKEJDV"
    valid_destination_memo_1 = ""
    valid_destination_2 = "GB5ZQJYKSZP3JOMOCWCBI7SPQUBW6ZL3642FUB7IYNAOC2EQMAFXI3P2"
    valid_destination_memo_2 = "starlight"
    valid_refund = "GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B"
    valid_refund_memo = ""
    valid_send_amount_1 = 10000000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100
    valid_fees_2 = 10078
    fake_refund = "abcdabcd"
    fake_refund_memo = ""
    fake_payout = "abcdabcd"
    fake_payout_memo = ""
    signature_refusal_error_code = StellarErrors.SW_SWAP_CHECKING_FAIL

    def perform_final_tx(self, destination, send_amount, fees, memo):
        StellarClient(self.backend).send_simple_sign_tx(path="m/44'/148'/0'",
                                                        network=Network.MAINNET,
                                                        fees=fees,
                                                        memo=memo,
                                                        destination=destination,
                                                        send_amount=send_amount)
        # TODO : assert signature validity


# Use a class to reuse the same Speculos instance
class TestsStellar:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_THORSWAP)
    def test_stellar(self, backend, exchange_navigation_helper, test_to_run):
        StellarTests(backend, exchange_navigation_helper).run_test(test_to_run)
