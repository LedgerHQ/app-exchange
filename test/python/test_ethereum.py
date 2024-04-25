import pytest
import os
import json
from web3 import Web3

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO
from .apps.ethereum import ETH_PATH
from ledger_app_clients.ethereum.client import EthAppClient
from .apps import cal as cal


# ExchangeTestRunner implementation for all Ethereum network
class GenericEthereumNetworkTests(ExchangeTestRunner):
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
        app_client = EthAppClient(self.backend)
        with app_client.sign(bip32_path=ETH_PATH,
                             tx_params={
                                 "nonce": 0,
                                 "gasPrice": 1,
                                 "gas": fees,
                                 "to": destination,
                                 "value": send_amount,
                                 "chainId": self.chain_id
                             }):
            pass
        # TODO : assert signature validity



# ExchangeTestRunner implementation for native ETH
class EthereumTests(GenericEthereumNetworkTests):
    chain_id = 1
    currency_configuration = cal.ETH_CURRENCY_CONFIGURATION

class TestsEthereum:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_ethereum(self, backend, exchange_navigation_helper, test_to_run):
        EthereumTests(backend, exchange_navigation_helper).run_test(test_to_run)



# ExchangeTestRunner implementation for BSC on ETH application
class BSCTests(GenericEthereumNetworkTests):
    chain_id = 56
    currency_configuration = cal.BNB_CURRENCY_CONFIGURATION

class TestsBSC:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_bsc(self, backend, exchange_navigation_helper, test_to_run):
        BSCTests(backend, exchange_navigation_helper).run_test(test_to_run)



# ExchangeTestRunner implementation for BSC on BNB application
class BSCLegacyTests(GenericEthereumNetworkTests):
    chain_id = 56
    currency_configuration = cal.BNB_LEGACY_CURRENCY_CONFIGURATION

class TestsBSCLegacy:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_bsc_legacy(self, backend, exchange_navigation_helper, test_to_run):
        BSCLegacyTests(backend, exchange_navigation_helper).run_test(test_to_run)



# ExchangeTestRunner implementation for Eth token DAI
class DAITests(GenericEthereumNetworkTests):
    currency_configuration = cal.DAI_CURRENCY_CONFIGURATION
    DAI_ADDRESS = bytes.fromhex("5d3a536e4d6dbd6114cc1ead35777bab948e3643")

    with open(f"{os.path.dirname(__file__)}/apps/erc20.json", encoding="utf-8") as file:
        contract = Web3().eth.contract(
            abi=json.load(file),
            address=DAI_ADDRESS
        )

    def perform_final_tx(self, destination, send_amount, fees, memo):
        app_client = EthAppClient(self.backend)
        app_client.provide_token_metadata("DAI", self.DAI_ADDRESS, 18, 1)
        with app_client.sign(bip32_path=ETH_PATH,
                             tx_params={
                                "nonce": 0,
                                "gasPrice": 1,
                                "gas": fees,
                                "to": self.contract.address,
                                "data": self.contract.encodeABI("transfer", [destination, send_amount]),
                                "chainId": 1
                             }):
            pass

class TestsDAI:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_dai(self, backend, exchange_navigation_helper, test_to_run):
        DAITests(backend, exchange_navigation_helper).run_test(test_to_run)
