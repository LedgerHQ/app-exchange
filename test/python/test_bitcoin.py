import pytest

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO
from .apps.bitcoin import BitcoinClient, BitcoinErrors
from ledger_bitcoin import WalletPolicy

in_wallet = WalletPolicy(
    "",
    "wpkh(@0/**)",
    [
        "[f5acc2fd/84'/0'/0']xpub6DUYn4moKgHkK2d7bXX3mHTPb6XQwRVFRMdZ6ZwLS5u3nonGVpJiFeZiQkHutwdFqxKP75jex8gvVm7ed4euYeDtMnoiF1Cz1z4CeBJYWin"
    ],
)

out_wallet = WalletPolicy(
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

# ExchangeTestRunner implementation for Bitcoin
class BitcoinTests(ExchangeTestRunner):

    currency_ticker = "BTC"
    valid_destination_1 = BitcoinClient.get_address_from_wallet(out_wallet)
    valid_destination_memo_1 = ""
    valid_destination_2 = BitcoinClient.get_address_from_wallet(out_wallet_2)
    valid_destination_memo_2 = "0"
    valid_refund = BitcoinClient.get_address_from_wallet(in_wallet)
    valid_refund_memo = ""
    valid_send_amount_1 = 20900000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100000
    valid_fees_2 = 10078
    fake_refund = "abcdabcd"
    fake_refund_memo = ""
    fake_payout = "abcdabcd"
    fake_payout_memo = ""
    signature_refusal_error_code = BitcoinErrors.SW_SWAP_CHECKING_FAIL

    def perform_final_tx(self, destination, send_amount, fees, memo):
        if destination == BitcoinClient.get_address_from_wallet(out_wallet):
            BitcoinClient(self.backend).send_simple_sign_tx(in_wallet=in_wallet,
                                                      fees=fees,
                                                      destination=out_wallet,
                                                      send_amount=send_amount)

        elif destination == BitcoinClient.get_address_from_wallet(out_wallet_2):
            BitcoinClient(self.backend).send_simple_sign_tx(in_wallet=in_wallet,
                                                      fees=fees,
                                                      destination=out_wallet_2,
                                                      send_amount=send_amount)

        # TODO : assert signature validity


# Use a class to reuse the same Speculos instance
class TestsBitcoin:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_bitcoin(self, backend, exchange_navigation_helper, test_to_run):
        BitcoinTests(backend, exchange_navigation_helper).run_test(test_to_run)

