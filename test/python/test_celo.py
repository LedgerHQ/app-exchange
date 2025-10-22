import pytest

from ledger_app_clients.exchange.test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_THORSWAP
from .apps.celo import Errors, CELO_PATH
from ledger_app_clients.ethereum.client import EthAppClient
from .apps import cal as cal



# ExchangeTestRunner implementation for all Ethereum network
class CeloTests(ExchangeTestRunner):
    valid_destination_1 = "0x79D5A290D7ba4b99322d91b577589e8d0BF87072"
    valid_destination_2 = "0x0a101aA5347Bb16F43019BE42ce5830395739e33"
    valid_refund = "0x197657b428707c304a5Ee9BA09aF7d13D17BF0D9"
    valid_send_amount_1 = 10000000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 101
    valid_fees_2 = 10078
    fake_refund = "abcdabcd"
    fake_payout = "abcdabcd"
    chain_id = 42220  # Celo mainnet chain ID

    signature_refusal_error_code = Errors.SW_SWAP_CHECKING_FAIL
    wrong_method_error_code = Errors.SW_SWAP_CHECKING_FAIL
    wrong_destination_error_code = Errors.SW_SWAP_CHECKING_FAIL
    wrong_amount_error_code = Errors.SW_SWAP_CHECKING_FAIL
    wrong_fees_error_code = Errors.SW_SWAP_CHECKING_FAIL
    
    # ####
    # # The coin configuration used for this currency
    currency_configuration = cal.CELO_CURRENCY_CONFIGURATION

    def perform_final_tx(self, destination, send_amount, fees, memo):
        app_client = EthAppClient(self.backend)
        with app_client.sign(bip32_path=CELO_PATH,
                    tx_params={
                    "nonce": 0,
                    'maxFeePerGas': 1,
                    'maxPriorityFeePerGas': 3,
                    "gas": fees,
                    "to": destination,
                    "value": send_amount,
                    "chainId": self.chain_id,
                    "type": 2,  # Add transaction type here (e.g., 2 for EIP-1559)
                    }):
            pass
        pass

class TestsCelo:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_THORSWAP)
    def test_celo(self, backend, exchange_navigation_helper, test_to_run):
        CeloTests(backend, exchange_navigation_helper).run_test(test_to_run)