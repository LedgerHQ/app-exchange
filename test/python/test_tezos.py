import pytest

from ledger_app_clients.exchange.test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP
from .apps.tezos import TezosClient, encode_address, XTZ_PACKED_DERIVATION_PATH, StatusCode
from .apps import cal as cal

from requests.exceptions import ChunkedEncodingError, ConnectionError
from urllib3.exceptions import ProtocolError
from http.client import IncompleteRead

# A bit hacky but way less hassle than actually writing an actual address decoder
TEZOS_ADDRESS_DECODER = {
    encode_address("e6330795ffe18f873b83cb13662442b87bd98c22"): "e6330795ffe18f873b83cb13662442b87bd98c22",
    encode_address("e6330795ffe18f873b83cb13662442b87bd98c40"): "e6330795ffe18f873b83cb13662442b87bd98c40",
}

# ExchangeTestRunner implementation for Stellar
class TezosTests(ExchangeTestRunner):
    currency_configuration = cal.XTZ_CURRENCY_CONFIGURATION
    valid_destination_1 = encode_address("e6330795ffe18f873b83cb13662442b87bd98c22")
    valid_destination_2 = encode_address("e6330795ffe18f873b83cb13662442b87bd98c40")
    valid_refund = "tz1YPjCVqgimTAPmxZX9egDeTFRCmrTRqmp9"
    valid_send_amount_1 = 10000000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100
    valid_fees_2 = 10078
    fake_refund = "abcdabcd"
    fake_payout = "abcdabcd"
    signature_refusal_error_code = StatusCode.EXC_REJECT

    def perform_final_tx(self, destination, send_amount, fees, memo):
        decoded_destination = TEZOS_ADDRESS_DECODER[destination]
        TezosClient(self.backend).send_simple_sign_tx(path=XTZ_PACKED_DERIVATION_PATH,
                                                      fees=fees,
                                                      memo=memo,
                                                      destination=decoded_destination,
                                                      send_amount=send_amount)

        # TODO : assert signature validity


# Use a class to reuse the same Speculos instance
class TestsTezos:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP)
    def test_tezos(self, backend, exchange_navigation_helper, test_to_run):
        TezosTests(backend, exchange_navigation_helper).run_test(test_to_run)
