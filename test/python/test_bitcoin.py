import pytest

from ledger_app_clients.exchange.client import PayinExtraDataID
from ledger_app_clients.exchange.test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO
from .apps.bitcoin import BitcoinClient, BitcoinErrors
from .apps import cal as cal
from ledger_bitcoin import WalletPolicy
from hashlib import sha256

in_wallet = WalletPolicy(
    "",
    "wpkh(@0/**)",
    [
        "[f5acc2fd/84'/0'/0']xpub6DUYn4moKgHkK2d7bXX3mHTPb6XQwRVFRMdZ6ZwLS5u3nonGVpJiFeZiQkHutwdFqxKP75jex8gvVm7ed4euYeDtMnoiF1Cz1z4CeBJYWin"
    ],
)

out_wallet_1 = WalletPolicy(
    "",
    "wpkh(@0/**)",
    [
        "xpub6CatWdiZiodmYVtWLtEQsAg1H9ooS1bmsJUBwQ83FE1Fyk386FWcyicJgEZv3quZSJKA5dh5Lo2PbubMGxCfZtRthV6ST2qquL9w3HSzcUn"
    ],
)

out_wallet_2 = WalletPolicy(
    "",
    "wpkh(@0/**)",
    [
        "xpub6D7atwj3ewAGT347tUzTNzfTGos1rCFVX4v8gViXiM2R1QHvox1LhEf6NtCeNsCwpppFUoQuS6mHUwfTveA5tEEwn2LqZHfVBEz5qvYmYhf"
    ],
)

opreturn_data_1 = bytes.fromhex("CAFE")
opreturn_data_2 = bytes.fromhex("CAFEDECA00DECA00CAFE00DEADBEEF123456789012345678901234567890123456789012345CAFEDECA00DECA00CAFE00DEADBEEF123456789012345678901234567890123456789012345")


# ExchangeTestRunner implementation for Bitcoin
class BitcoinTests(ExchangeTestRunner):

    currency_configuration = cal.BTC_CURRENCY_CONFIGURATION
    valid_destination_1 = BitcoinClient.get_address_from_wallet(out_wallet_1)
    valid_destination_2 = BitcoinClient.get_address_from_wallet(out_wallet_2)
    valid_refund = BitcoinClient.get_address_from_wallet(in_wallet)
    valid_send_amount_1 = 20900000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100000
    valid_fees_2 = 10078
    fake_refund = "abcdabcd"
    fake_payout = "abcdabcd"
    signature_refusal_error_code = BitcoinErrors.SW_SWAP_CHECKING_FAIL
    valid_payin_extra_data_1 = PayinExtraDataID.OP_RETURN.to_bytes(1, byteorder='big') + sha256(opreturn_data_1).digest()
    valid_payin_extra_data_2 = PayinExtraDataID.OP_RETURN.to_bytes(1, byteorder='big') + sha256(opreturn_data_2).digest()
    invalid_payin_extra_data = PayinExtraDataID.EVM_CALLDATA.to_bytes(1, byteorder='big') + sha256(opreturn_data_1).digest()

    def perform_final_tx(self, destination, send_amount, fees, memo):
        if destination == self.valid_destination_1:
            wallet = out_wallet_1
        elif destination == self.valid_destination_2:
            wallet = out_wallet_2
        else:
            assert False

        if memo == self.valid_payin_extra_data_1:
            opreturn_data = opreturn_data_1
        elif memo == self.valid_payin_extra_data_2:
            opreturn_data = opreturn_data_2
        elif memo == self.invalid_payin_extra_data:
            opreturn_data = opreturn_data_1
        else:
            opreturn_data = None

        BitcoinClient(self.backend).send_simple_sign_tx(in_wallet=in_wallet,
                                                        fees=fees,
                                                        destination=wallet,
                                                        send_amount=send_amount,
                                                        opreturn_data=opreturn_data)

        # TODO : assert signature validity


# Use a class to reuse the same Speculos instance
class TestsBitcoin:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_bitcoin(self, backend, exchange_navigation_helper, test_to_run):
        BitcoinTests(backend, exchange_navigation_helper).run_test(test_to_run)
