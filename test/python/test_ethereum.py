import pytest

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO
from .apps.ethereum import ETH_PATH
from ledger_app_clients.ethereum.client import EthAppClient
from .apps import cal as cal


# ExchangeTestRunner implementation for Ethereum
class EthereumTests(ExchangeTestRunner):
    currency_configuration = cal.ETH_CURRENCY_CONFIGURATION
    valid_destination_1 = "0xd692Cb1346262F584D17B4B470954501f6715a82"
    valid_destination_memo_1 = ""
    valid_destination_2 = "0x999999cf1046e68e36E1aA2E0E07105eDDD1f08E"
    valid_destination_memo_2 = ""
    valid_refund = "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D"
    valid_refund_memo = ""
    valid_send_amount_1 = 10000000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100
    valid_fees_2 = 10078
    fake_refund = "abcdabcd"
    fake_refund_memo = ""
    fake_payout = "abcdabcd"
    fake_payout_memo = ""
    signature_refusal_error_code = 0x6001

    def perform_final_tx(self, destination, send_amount, fees, memo):
        print("perform_final_tx")
        print(f"{destination}")
        app_client = EthAppClient(self.backend)
        with app_client.sign(bip32_path=ETH_PATH,
                             tx_params={
                                 "nonce": 0,
                                 "gasPrice": 1,
                                 "gas": fees,
                                 "to": destination,
                                 "value": send_amount,
                                 "chainId": 1
                             }):
            pass
        # TODO : assert signature validity

# Use a class to reuse the same Speculos instance
class TestsEthereum:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_ethereum(self, backend, exchange_navigation_helper, test_to_run):
        EthereumTests(backend, exchange_navigation_helper).run_test(test_to_run)
