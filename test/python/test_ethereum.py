import pytest
import os
import json
from web3 import Web3

from ledger_app_clients.exchange.client import PayinExtraDataID
from ledger_app_clients.exchange.test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO, ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP
from .apps.ethereum import ETH_PATH
from ledger_app_clients.ethereum.client import EthAppClient
from .apps import cal as cal
from hashlib import sha256

contract_1 = bytes.fromhex("088890dc\
                            00000000000000000000000000000000000000000000000007252cc4958aa2f5\
                            00000000000000000000000000000000000000000000000000000000000000a0\
                            000000000000000000000000ac83cc67a4194f6f096813d0e1db323a358f8b28\
                            000000000000000000000000000000000000000000000000000000006673fce0\
                            0000000000000000000000005c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f\
                            0000000000000000000000000000000000000000000000000000000000000002\
                            000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2\
                            000000000000000000000000286675fed193e3cfb20bfa3ba12db56e9231a0f7")

# Different selector
contract_2 = bytes.fromhex("088890aa\
                            00000000000000000000000000000000000000000000000007252cc4958aa2f5\
                            00000000000000000000000000000000000000000000000000000000000000a0\
                            000000000000000000000000ac83cc67a4194f6f096813d0e1db323a358f8b28\
                            000000000000000000000000000000000000000000000000000000006673fce0\
                            0000000000000000000000005c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f\
                            0000000000000000000000000000000000000000000000000000000000000002\
                            000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2\
                            000000000000000000000000286675fed193e3cfb20bfa3ba12db56e9231a0f7")

# ExchangeTestRunner implementation for all Ethereum network
class GenericEthereumNetworkTests(ExchangeTestRunner):
    valid_destination_1 = "0xd692Cb1346262F584D17B4B470954501f6715a82"
    valid_destination_2 = "0x999999cf1046e68e36E1aA2E0E07105eDDD1f08E"
    valid_refund = "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D"
    valid_send_amount_1 = 10000000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100
    valid_fees_2 = 10078
    fake_refund = "abcdabcd"
    fake_payout = "abcdabcd"
    signature_refusal_error_code = 0x6001
    valid_payin_extra_data_1 = PayinExtraDataID.EVM_CALLDATA.to_bytes(1, byteorder='big') + sha256(contract_1).digest()
    valid_payin_extra_data_2 = PayinExtraDataID.EVM_CALLDATA.to_bytes(1, byteorder='big') + sha256(contract_2).digest()
    invalid_payin_extra_data = PayinExtraDataID.OP_RETURN.to_bytes(1, byteorder='big') + sha256(contract_1).digest()

    def perform_final_tx(self, destination, send_amount, fees, memo):
        app_client = EthAppClient(self.backend)

        if memo == self.valid_payin_extra_data_1:
            contract = contract_1
        elif memo == self.valid_payin_extra_data_2:
            contract = contract_2
        elif memo == self.invalid_payin_extra_data:
            contract = contract_1
        else:
            contract = None

        if contract == None:
            with app_client.sign(bip32_path=ETH_PATH,
                                 tx_params={
                                     "nonce": 0,
                                     "gasPrice": 1,
                                     "gas": fees,
                                     "to": destination,
                                     "value": send_amount,
                                     "chainId": self.chain_id,
                                 }):
                pass
        else:
            with app_client.sign(bip32_path=ETH_PATH,
                                 tx_params={
                                     "nonce": 0,
                                     "gasPrice": 1,
                                     "gas": fees,
                                     "to": destination,
                                     "value": send_amount,
                                     "chainId": self.chain_id,
                                     "data": contract,
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

        if memo == self.valid_payin_extra_data_1:
            contract = contract_1
        elif memo == self.valid_payin_extra_data_2:
            contract = contract_2
        elif memo == self.invalid_payin_extra_data:
            contract = contract_1
        else:
            contract = None

        if contract == None:
            app_client.provide_token_metadata("DAI", self.DAI_ADDRESS, 18, 1)
            with app_client.sign(bip32_path=ETH_PATH,
                                 tx_params={
                                    "nonce": 0,
                                    "gasPrice": 1,
                                    "gas": fees,
                                    "to": self.contract.address,
                                    "chainId": 1,
                                    "data": self.contract.encode_abi("transfer", [destination, send_amount]),
                                 }):
                pass
        else:
            with app_client.sign(bip32_path=ETH_PATH,
                                 tx_params={
                                     "nonce": 0,
                                     "gasPrice": 1,
                                     "gas": fees,
                                     "to": destination,
                                     "value": 0,
                                     "chainId": 1,
                                     "data": contract,
                                 }):
                pass

class TestsDAI:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_dai(self, backend, exchange_navigation_helper, test_to_run):
        DAITests(backend, exchange_navigation_helper).run_test(test_to_run)
