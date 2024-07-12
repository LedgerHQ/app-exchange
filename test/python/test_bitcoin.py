import pytest

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO
from .apps.bitcoin import BitcoinClient, BitcoinErrors
from .apps import cal as cal
from ledger_bitcoin import WalletPolicy

# ExchangeTestRunner implementation for Bitcoin
class BitcoinTestsCommon(ExchangeTestRunner):
    valid_destination_memo_1 = ""
    valid_destination_memo_2 = "0"
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
        if destination == BitcoinClient.get_address_from_wallet(self.out_wallet):
            BitcoinClient(self.backend).send_simple_sign_tx(in_wallet=self.in_wallet,
                                                            fees=fees,
                                                            destination=self.out_wallet,
                                                            send_amount=send_amount)

        elif destination == BitcoinClient.get_address_from_wallet(self.out_wallet_2):
            BitcoinClient(self.backend).send_simple_sign_tx(in_wallet=self.in_wallet,
                                                            fees=fees,
                                                            destination=self.out_wallet_2,
                                                            send_amount=send_amount)

        # TODO : assert signature validity


class BitcoinTests(BitcoinTestsCommon):
    currency_configuration = cal.BTC_CURRENCY_CONFIGURATION
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
    valid_refund = BitcoinClient.get_address_from_wallet(in_wallet)
    valid_destination_1 = BitcoinClient.get_address_from_wallet(out_wallet)
    valid_destination_2 = BitcoinClient.get_address_from_wallet(out_wallet_2)

class TestsBitcoin:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_bitcoin(self, backend, exchange_navigation_helper, test_to_run):
        BitcoinTests(backend, exchange_navigation_helper).run_test(test_to_run)


class BitcoinTestsSegwit(BitcoinTestsCommon):
    currency_configuration = cal.BTC_SEGWIT_CURRENCY_CONFIGURATION
    in_wallet = WalletPolicy(
        "",
        "sh(wpkh(@0/**))",
        [
            "[f5acc2fd/84'/0'/0']xpub6DUYn4moKgHkK2d7bXX3mHTPb6XQwRVFRMdZ6ZwLS5u3nonGVpJiFeZiQkHutwdFqxKP75jex8gvVm7ed4euYeDtMnoiF1Cz1z4CeBJYWin"
        ],
    )

    out_wallet = WalletPolicy(
        "",
        "sh(wpkh(@0/**))",
        [
            "ypub6Ynvx7RLNYgWzFGM8aeU43hFNjTh7u5Grrup7Ryu2nKZ1Y8FWKaJZXiUrkJSnMmGVNBoVH1DNDtQ32tR4YFDRSpSUXjjvsiMnCvoPHVWXJP"
        ],
    )

    out_wallet_2 = WalletPolicy(
        "",
        "sh(wpkh(@0/**))",
        [
            "xpub6D7atwj3ewAGT347tUzTNzfTGos1rCFVX4v8gViXiM2R1QHvox1LhEf6NtCeNsCwpppFUoQuS6mHUwfTveA5tEEwn2LqZHfVBEz5qvYmYhf"
        ],
    )
    valid_refund = BitcoinClient.get_address_from_wallet(in_wallet)
    valid_destination_1 = BitcoinClient.get_address_from_wallet(out_wallet)
    valid_destination_2 = BitcoinClient.get_address_from_wallet(out_wallet_2)


class TestsBitcoinSegwit:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_bitcoin_segwit(self, backend, exchange_navigation_helper, test_to_run):
        BitcoinTestsSegwit(backend, exchange_navigation_helper).run_test(test_to_run)


class BitcoinTestsTaproot(BitcoinTestsCommon):
    currency_configuration = cal.BTC_TAPROOT_CURRENCY_CONFIGURATION
    in_wallet = WalletPolicy(
        "",
        "tr(@0/**)",
        [
            "[f5acc2fd/86'/0'/0']xpub6DUYn4moKgHkK2d7bXX3mHTPb6XQwRVFRMdZ6ZwLS5u3nonGVpJiFeZiQkHutwdFqxKP75jex8gvVm7ed4euYeDtMnoiF1Cz1z4CeBJYWin"
        ],
    )

    out_wallet = WalletPolicy(
        "",
        "tr(@0/**)",
        [
            "[f5acc2fd/86'/1'/0']tpubDDKYE6BREvDsSWMazgHoyQWiJwYaDDYPbCFjYxN3HFXJP5fokeiK4hwK5tTLBNEDBwrDXn8cQ4v9b2xdW62Xr5yxoQdMu1v6c7UDXYVH27U"
        ],
    )

    out_wallet_2 = WalletPolicy(
        "",
        "tr(@0/**)",
        [
            "xpub6D7atwj3ewAGT347tUzTNzfTGos1rCFVX4v8gViXiM2R1QHvox1LhEf6NtCeNsCwpppFUoQuS6mHUwfTveA5tEEwn2LqZHfVBEz5qvYmYhf"
        ],
    )
    valid_refund = BitcoinClient.get_address_from_wallet(in_wallet)
    valid_destination_1 = BitcoinClient.get_address_from_wallet(out_wallet)
    valid_destination_2 = BitcoinClient.get_address_from_wallet(out_wallet_2)

class TestsBitcoinTaproot:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO)
    def test_bitcoin_taproot(self, backend, exchange_navigation_helper, test_to_run):
        BitcoinTestsTaproot(backend, exchange_navigation_helper).run_test(test_to_run)

