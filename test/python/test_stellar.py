import pytest
from typing import Optional, Tuple

from ragger.backend import RaisePolicy
from ragger.utils import RAPDU
from ragger.error import ExceptionRAPDU
from ragger.navigator import NavInsID

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors
from .apps.stellar import Network, StellarClient, StellarErrors

from .signing_authority import SigningAuthority, LEDGER_SIGNER

from .utils import ROOT_SCREENSHOT_PATH, handle_lib_call_start_or_stop


def test_stellar_wrong_refund(backend):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "payin_address": b"GCKUD4BHIYSAYHU7HBB5FDSW6CSYH3GSOUBPWD2KE7KNBERP4BSKEJDV",
        "payin_extra_id": b"starlight",
        "refund_address": b"abcdabcd",
        "refund_extra_id": b"",
        "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "payout_extra_id": b"",
        "currency_from": "XLM",
        "currency_to": "ETH",
        "amount_to_provider": int.to_bytes(1000, length=8, byteorder='big'),
        "amount_to_wallet": b"\246\333t\233+\330\000",
    }
    fees_bytes = int.to_bytes(100, length=4, byteorder='big')
    ex.process_transaction(tx_infos, fees_bytes)
    ex.check_transaction_signature(partner)

    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER):
        pass
    assert ex.get_check_address_response().status == Errors.INVALID_ADDRESS


def test_stellar_wrong_payout(backend):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "payin_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "payin_extra_id": b"",
        "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "refund_extra_id": b"",
        "payout_address": b"abcdabcd",
        "payout_extra_id": b"",
        "currency_from": "ETH",
        "currency_to": "XLM",
        "amount_to_provider": int.to_bytes(1000, length=8, byteorder='big'),
        "amount_to_wallet": b"\246\333t\233+\330\000",
    }
    fees_bytes = int.to_bytes(100, length=4, byteorder='big')
    ex.process_transaction(tx_infos, fees_bytes)
    ex.check_transaction_signature(partner)

    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER):
        pass
    assert ex.get_check_address_response().status == Errors.INVALID_ADDRESS


class StellarValidTxPerformer:
    # Default valid tx values used for the tests
    def_path = "m/44'/148'/0'"
    def_fees = 100
    def_memo = ""
    def_destination = "GCKUD4BHIYSAYHU7HBB5FDSW6CSYH3GSOUBPWD2KE7KNBERP4BSKEJDV"
    def_send_amount = 10000000

    # Helper to use default args if none provided
    def _maybe_default(self, fees, memo, destination, send_amount) -> Tuple[int, str, str, int]:
        fees = self.def_fees if fees is None else fees
        memo = self.def_memo if memo is None else memo
        destination = self.def_destination if destination is None else destination
        send_amount = self.def_send_amount if send_amount is None else send_amount
        return (fees, memo, destination, send_amount)

    # Helper to send a valid TX to the Stellar app, provide parameters to overload te default values
    def perform_stellar_tx(self,
                           backend,
                           fees: Optional[int]=None,
                           memo: Optional[str]=None,
                           destination: Optional[str]=None,
                           send_amount: Optional[int]=None) -> RAPDU:
        fees, memo, destination, send_amount = self._maybe_default(fees, memo, destination, send_amount)

        rapdu = StellarClient(backend).send_simple_sign_tx(path=self.def_path,
                                                           network=Network.MAINNET,
                                                           fees=fees,
                                                           memo=memo,
                                                           destination=destination,
                                                           send_amount=send_amount)
        # TODO : assert signature validity

        handle_lib_call_start_or_stop(backend)
        return rapdu

    def perform_valid_exchange_tx(self, backend, navigator, test_name, subcommand, tx_infos, fees):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=ex.partner_curve, name="Default name")
        ex.init_transaction()
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        fees_bytes = int.to_bytes(fees, length=4, byteorder='big')
        ex.process_transaction(tx_infos, fees_bytes)
        ex.check_transaction_signature(partner)
        with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER):
            if backend.firmware.device.startswith("nano"):
                navigator.navigate_until_text_and_compare(NavInsID.RIGHT_CLICK,
                                                          [NavInsID.BOTH_CLICK],
                                                          "Accept",
                                                          ROOT_SCREENSHOT_PATH,
                                                          test_name)
            else:
                navigator.navigate_until_text_and_compare(NavInsID.USE_CASE_REVIEW_TAP,
                                                          [NavInsID.USE_CASE_REVIEW_CONFIRM],
                                                          "Hold to sign",
                                                          ROOT_SCREENSHOT_PATH,
                                                          test_name)
        ex.start_signing_transaction()


##############
# SWAP tests #
##############

class StellarValidSwapPerformer(StellarValidTxPerformer):
    # Helper to send a valid SWAP TX to the Exchange app, provide parameters to overload te default values
    def perform_valid_swap(self,
                           backend,
                           navigator,
                           test_name,
                           fees: Optional[int]=None,
                           memo: Optional[str]=None,
                           destination: Optional[str]=None,
                           send_amount: Optional[int]=None):
        fees, memo, destination, send_amount = self._maybe_default(fees, memo, destination, send_amount)
        tx_infos = {
            "payin_address": destination,
            "payin_extra_id": memo.encode(),
            "refund_address": b"GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B",
            "refund_extra_id": b"",
            "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
            "payout_extra_id": b"",
            "currency_from": "XLM",
            "currency_to": "ETH",
            "amount_to_provider": int.to_bytes(send_amount, length=8, byteorder='big'),
            "amount_to_wallet": b"\246\333t\233+\330\000",
        }
        self.perform_valid_exchange_tx(backend, navigator, test_name, SubCommand.SWAP, tx_infos, fees)

from time import sleep
# Valid swap test with default values
def test_stellar_swap_valid_1(backend, navigator, test_name):
    performer = StellarValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    sleep(5)
    performer.perform_stellar_tx(backend)


# Valid swap test with non default values
def test_stellar_swap_valid_2(backend, navigator, test_name):
    fees = 10078
    memo = "starlight"
    destination = "GB5ZQJYKSZP3JOMOCWCBI7SPQUBW6ZL3642FUB7IYNAOC2EQMAFXI3P2"
    send_amount = 446739662

    performer = StellarValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name, fees=fees, memo=memo, destination=destination, send_amount=send_amount)
    performer.perform_stellar_tx(backend, fees=fees, memo=memo, destination=destination, send_amount=send_amount)


# Make a valid swap and then ask a second signature
def test_stellar_swap_refuse_double_sign(backend, navigator, test_name):
    performer = StellarValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    performer.perform_stellar_tx(backend)

    with pytest.raises(ExceptionRAPDU) as e:
        performer.perform_stellar_tx(backend)
    assert e.value.status == Errors.INVALID_INSTRUCTION


# Test swap with a malicious Stellar TX with tampered fees
def test_stellar_swap_wrong_fees(backend, navigator, test_name):
    performer = StellarValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, fees=performer.def_fees + 100)
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


# Test swap with a malicious Stellar TX with tampered memo
def test_stellar_swap_wrong_memo(backend, navigator, test_name):
    performer = StellarValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, memo=performer.def_memo + "0")
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


# Test swap with a malicious Stellar TX with tampered dest
def test_stellar_swap_wrong_dest(backend, navigator, test_name):
    performer = StellarValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, destination="GB5ZQJYKSZP3JOMOCWCBI7SPQUBW6ZL3642FUB7IYNAOC2EQMAFXI3P2")
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


# Test swap with a malicious Stellar TX with tampered amount
def test_stellar_swap_wrong_amount(backend, navigator, test_name):
    performer = StellarValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, send_amount=performer.def_send_amount + 351)
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


##############
# FUND tests #
##############

class StellarValidFundPerformer(StellarValidTxPerformer):
    # Helper to send a valid FUND TX to the Exchange app, provide parameters to overload te default values
    def perform_valid_fund(self,
                           backend,
                           navigator,
                           test_name,
                           fees: Optional[int]=None,
                           memo: Optional[str]=None,
                           destination: Optional[str]=None,
                           send_amount: Optional[int]=None):
        fees, memo, destination, send_amount = self._maybe_default(fees, memo, destination, send_amount)
        tx_infos = {
            "user_id": "Jon Wick",
            "account_name": "My account 00",
            "in_currency": "XLM",
            "in_amount": int.to_bytes(send_amount, length=4, byteorder='big'),
            "in_address": destination,
        }
        self.perform_valid_exchange_tx(backend, navigator, test_name, SubCommand.FUND, tx_infos, fees)


# Valid fund test with default values
def test_stellar_fund_valid_1(backend, navigator, test_name):
    performer = StellarValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    performer.perform_stellar_tx(backend)
    sleep(5)


# Valid fund test with non default values
def test_stellar_fund_valid_2(backend, navigator, test_name):
    fees = 10078
    destination="GB5ZQJYKSZP3JOMOCWCBI7SPQUBW6ZL3642FUB7IYNAOC2EQMAFXI3P2"
    send_amount = 446739662

    performer = StellarValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name, fees=fees, destination=destination, send_amount=send_amount)
    performer.perform_stellar_tx(backend, fees=fees, destination=destination, send_amount=send_amount)


# Make a valid fund and then ask a second signature
def test_stellar_fund_refuse_double_sign(backend, navigator, test_name):
    performer = StellarValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    performer.perform_stellar_tx(backend)

    with pytest.raises(ExceptionRAPDU) as e:
        performer.perform_stellar_tx(backend)
    assert e.value.status == Errors.INVALID_INSTRUCTION


# Test fund with a malicious Stellar TX with tampered fees
def test_stellar_fund_wrong_fees(backend, navigator, test_name):
    performer = StellarValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, fees=performer.def_fees + 100)
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL
    sleep(10)


# Test fund with a malicious Stellar TX with tampered memo
def test_stellar_fund_wrong_memo(backend, navigator, test_name):
    performer = StellarValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, memo=performer.def_memo + "0")
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


# Test fund with a malicious Stellar TX with tampered dest
def test_stellar_fund_wrong_dest(backend, navigator, test_name):
    performer = StellarValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, destination="GB5ZQJYKSZP3JOMOCWCBI7SPQUBW6ZL3642FUB7IYNAOC2EQMAFXI3P2")
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


# Test fund with a malicious Stellar TX with tampered amount
def test_stellar_fund_wrong_amount(backend, navigator, test_name):
    performer = StellarValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, send_amount=performer.def_send_amount + 351)
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


##############
# SELL tests #
##############

class StellarValidSellPerformer(StellarValidTxPerformer):
    # Helper to send a valid SELL TX to the Exchange app, provide parameters to overload te default values
    def perform_valid_sell(self,
                           backend,
                           navigator,
                           test_name,
                           fees: Optional[int]=None,
                           memo: Optional[str]=None,
                           destination: Optional[str]=None,
                           send_amount: Optional[int]=None):
        fees, memo, destination, send_amount = self._maybe_default(fees, memo, destination, send_amount)
        tx_infos = {
            "trader_email": "john@doe.lost",
            "out_currency": "USD",
            "out_amount": {"coefficient": b"\x01", "exponent": 3},
            "in_currency": "XLM",
            "in_amount": int.to_bytes(send_amount, length=4, byteorder='big'),
            "in_address": destination,
        }
        self.perform_valid_exchange_tx(backend, navigator, test_name, SubCommand.SELL, tx_infos, fees)


# Valid sell test with default values
def test_stellar_sell_valid_1(backend, navigator, test_name):
    performer = StellarValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    performer.perform_stellar_tx(backend)


# Valid sell test with non default values
def test_stellar_sell_valid_2(backend, navigator, test_name):
    fees = 10078
    destination="GB5ZQJYKSZP3JOMOCWCBI7SPQUBW6ZL3642FUB7IYNAOC2EQMAFXI3P2"
    send_amount = 446739662

    performer = StellarValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name, fees=fees, destination=destination, send_amount=send_amount)
    performer.perform_stellar_tx(backend, fees=fees, destination=destination, send_amount=send_amount)


# Make a valid sell and then ask a second signature
def test_stellar_sell_refuse_double_sign(backend, navigator, test_name):
    performer = StellarValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    performer.perform_stellar_tx(backend)

    with pytest.raises(ExceptionRAPDU) as e:
        performer.perform_stellar_tx(backend)
    assert e.value.status == Errors.INVALID_INSTRUCTION


# Test sell with a malicious Stellar TX with tampered fees
def test_stellar_sell_wrong_fees(backend, navigator, test_name):
    performer = StellarValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, fees=performer.def_fees + 100)
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


# Test sell with a malicious Stellar TX with tampered memo
def test_stellar_sell_wrong_memo(backend, navigator, test_name):
    performer = StellarValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, memo=performer.def_memo + "0")
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


# Test sell with a malicious Stellar TX with tampered dest
def test_stellar_sell_wrong_dest(backend, navigator, test_name):
    performer = StellarValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, destination="GB5ZQJYKSZP3JOMOCWCBI7SPQUBW6ZL3642FUB7IYNAOC2EQMAFXI3P2")
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL


# Test sell with a malicious Stellar TX with tampered amount
def test_stellar_sell_wrong_amount(backend, navigator, test_name):
    performer = StellarValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_stellar_tx(backend, send_amount=performer.def_send_amount + 351)
    assert rapdu.status == StellarErrors.SW_SWAP_CHECKING_FAIL
