import pytest

from ragger.error import ExceptionRAPDU

from .apps.exchange_test_runner import ExchangeTestRunner
from .apps.exchange_test_runner import VALID_TESTS, ALL_TESTS_EXCEPT_FEES
from .apps.tron import TronClient, TronErrors
from .apps import cal as cal


# ExchangeTestRunner implementation for Tron
class TronTests(ExchangeTestRunner):
    valid_destination_1 = "TNbtZSpknaQvC7jPCLU4znJMgm8fhuGTTY"
    valid_destination_memo_1 = ""
    valid_destination_2 = "TBoTZcARzWVgnNuB9SyE3S5g1RwsXoQL16"
    valid_destination_memo_2 = ""
    valid_refund = "TNbtZSpknaQvC7jPCLU4znJMgm8fhuGTTY"
    valid_refund_memo = ""
    valid_send_amount_1 = 1000000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 0
    valid_fees_2 = 1
    fake_refund = "abcdabcd"
    fake_refund_memo = "1"
    fake_payout = "abcdabcd"
    fake_payout_memo = "1"
    signature_refusal_error_code = TronErrors.SW_SWAP_CHECKING_FAIL


##################################################
# ExchangeTestRunner implementation for Tron TRX #
##################################################
class TronTrxTests(TronTests):
    currency_configuration = cal.TRX_CURRENCY_CONFIGURATION

    def perform_final_tx(self, destination, send_amount, fees, memo):
        TronClient(self.backend).send_tx(path="m/44'/148'/0'",
                                         memo=memo,
                                         destination=destination,
                                         send_amount=send_amount,
                                         token="TRX")
        # TODO : assert signature validity


class TestsTrx:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_FEES)
    def test_tron_trx(self, backend, exchange_navigation_helper, test_to_run):
        TronTrxTests(backend, exchange_navigation_helper).run_test(test_to_run)


###################################################
# ExchangeTestRunner implementation for Tron USDT #
###################################################
class TronUsdtTests(TronTests):
    currency_configuration = cal.USDT_CURRENCY_CONFIGURATION

    def perform_final_tx(self, destination, send_amount, fees, memo):
        TronClient(self.backend).send_tx(path="m/44'/148'/0'",
                                         memo=memo,
                                         destination=destination,
                                         send_amount=send_amount,
                                         token="USDT")
        # TODO : assert signature validity


class TestsUsdt:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_FEES)
    def test_tron_usdt(self, backend, exchange_navigation_helper, test_to_run):
        TronUsdtTests(backend, exchange_navigation_helper).run_test(test_to_run)


###################################################
# ExchangeTestRunner implementation for Tron USDC #
###################################################
class TronUsdcTests(TronTests):
    currency_configuration = cal.USDC_CURRENCY_CONFIGURATION

    def perform_final_tx(self, destination, send_amount, fees, memo):
        TronClient(self.backend).send_tx(path="m/44'/148'/0'",
                                         memo=memo,
                                         destination=destination,
                                         send_amount=send_amount,
                                         token="USDC")
        # TODO : assert signature validity


class TestsUsdc:
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_FEES)
    def test_tron_usdc(self, backend, exchange_navigation_helper, test_to_run):
        TronUsdcTests(backend, exchange_navigation_helper).run_test(test_to_run)


#####################################################################
# ExchangeTestRunner implementation for Tron TRX but wrong tx token #
#####################################################################
class TronTrxToUsdtTests(TronTests):
    currency_configuration = cal.TRX_CURRENCY_CONFIGURATION

    def perform_final_tx(self, destination, send_amount, fees, memo):
        with pytest.raises(ExceptionRAPDU) as e:
            TronClient(self.backend).send_tx(path="m/44'/148'/0'",
                                             memo=memo,
                                             destination=destination,
                                             send_amount=send_amount,
                                             token="USDT")
        assert e.value.status == self.signature_refusal_error_code


class TestsTRXToUsdt:
    @pytest.mark.parametrize('test_to_run', VALID_TESTS)
    def test_tron_trx_to_usdt(self, backend, exchange_navigation_helper, test_to_run):
        TronTrxToUsdtTests(backend, exchange_navigation_helper).run_test(test_to_run)


############################################################################
# ExchangeTestRunner implementation for Tron USDT but wrong tx token (TRX) #
############################################################################
class TronUsdttoTrxTests(TronTests):
    currency_configuration = cal.USDT_CURRENCY_CONFIGURATION

    def perform_final_tx(self, destination, send_amount, fees, memo):
        with pytest.raises(ExceptionRAPDU) as e:
            TronClient(self.backend).send_tx(path="m/44'/148'/0'",
                                             memo=memo,
                                             destination=destination,
                                             send_amount=send_amount,
                                             token="TRX")
        assert e.value.status == self.signature_refusal_error_code


class TestsUsdtToTrx:
    @pytest.mark.parametrize('test_to_run', VALID_TESTS)
    def test_tron_usdt_to_trx(self, backend, exchange_navigation_helper, test_to_run):
        TronUsdttoTrxTests(backend, exchange_navigation_helper).run_test(test_to_run)


#############################################################################
# ExchangeTestRunner implementation for Tron USDT but wrong tx token (USDC) #
#############################################################################
class TronUsdtoUsdcTests(TronTests):
    currency_configuration = cal.USDT_CURRENCY_CONFIGURATION

    def perform_final_tx(self, destination, send_amount, fees, memo):
        with pytest.raises(ExceptionRAPDU) as e:
            TronClient(self.backend).send_tx(path="m/44'/148'/0'",
                                             memo=memo,
                                             destination=destination,
                                             send_amount=send_amount,
                                             token="USDC")
        assert e.value.status == self.signature_refusal_error_code


class TestsUsdtToUsdc:
    @pytest.mark.parametrize('test_to_run', VALID_TESTS)
    def test_tron_usdt_to_usdc(self, backend, exchange_navigation_helper, test_to_run):
        TronUsdtoUsdcTests(backend, exchange_navigation_helper).run_test(test_to_run)
