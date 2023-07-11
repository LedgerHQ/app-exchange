import pytest
from typing import Optional, Tuple

from ragger.backend import RaisePolicy
from ragger.utils import pack_APDU, RAPDU
from ragger.error import ExceptionRAPDU

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors
from .apps.xrp import XRPClient, DEFAULT_PATH, XRP_PACKED_DERIVATION_PATH, RippleErrors

from .signing_authority import SigningAuthority, LEDGER_SIGNER

from .utils import handle_lib_call_start_or_stop


def test_ripple_wrong_refund(backend):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "payin_address": b"ra7Zr8ddy9tB88RaXL8B87YkqhEJG2vkAJ",
        "payin_extra_id": b"",
        "refund_address": b"abcdabcd",
        "refund_extra_id": b"",
        "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "payout_extra_id": b"",
        "currency_from": "XRP",
        "currency_to": "ETH",
        "amount_to_provider": int.to_bytes(1000, length=8, byteorder='big'),
        "amount_to_wallet": b"\246\333t\233+\330\000",
    }
    ex.process_transaction(tx_infos, 100)
    ex.check_transaction_signature(partner)

    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER):
        pass
    assert ex.get_check_address_response().status == Errors.INVALID_ADDRESS


def test_ripple_wrong_payout(backend):
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
        "currency_to": "XRP",
        "amount_to_provider": int.to_bytes(1000, length=8, byteorder='big'),
        "amount_to_wallet": b"\246\333t\233+\330\000",
    }
    ex.process_transaction(tx_infos, 100)
    ex.check_transaction_signature(partner)

    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER):
        pass
    assert ex.get_check_address_response().status == Errors.INVALID_ADDRESS


class RippleValidTxPerformer:
    # Default valid tx values used for the tests
    def_path = "m/44'/144'/0'/0'/0"
    def_fees = 100
    def_memo = "0"
    def_destination = "ra7Zr8ddy9tB88RaXL8B87YkqhEJG2vkAJ"
    def_send_amount = 1000000

    # Helper to use default args if none provided
    def _maybe_default(self, fees, memo, destination, send_amount) -> Tuple[int, str, str, int]:
        fees = self.def_fees if fees is None else fees
        memo = self.def_memo if memo is None else memo
        destination = self.def_destination if destination is None else destination
        send_amount = self.def_send_amount if send_amount is None else send_amount
        return (fees, memo, destination, send_amount)

    # Helper to send a valid TX to the Ripple app, provide parameters to overload te default values
    def perform_ripple_tx(self,
                           backend,
                           fees: Optional[int]=None,
                           memo: Optional[str]=None,
                           destination: Optional[str]=None,
                           send_amount: Optional[int]=None) -> RAPDU:
        fees, memo, destination, send_amount = self._maybe_default(fees, memo, destination, send_amount)

        rapdu = XRPClient(backend).send_simple_sign_tx(path=self.def_path,
                                                       fees=fees,
                                                       memo=memo,
                                                       destination=destination,
                                                       send_amount=send_amount)
        # TODO : assert signature validity

        handle_lib_call_start_or_stop(backend)
        return rapdu

    def perform_valid_exchange_tx(self, backend, exchange_navigation_helper, subcommand, tx_infos, fees):
        ex = ExchangeClient(backend, Rate.FIXED, subcommand)
        partner = SigningAuthority(curve=ex.partner_curve, name="Default name")
        ex.init_transaction()
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        ex.process_transaction(tx_infos, fees)
        ex.check_transaction_signature(partner)
        with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER):
            exchange_navigation_helper.simple_accept()
        ex.start_signing_transaction()


##############
# SWAP tests #
##############

class RippleValidSwapPerformer(RippleValidTxPerformer):
    # Helper to send a valid SWAP TX to the Exchange app, provide parameters to overload te default values
    def perform_valid_swap(self,
                           backend,
                           exchange_navigation_helper,
                           fees: Optional[int]=None,
                           memo: Optional[str]=None,
                           destination: Optional[str]=None,
                           send_amount: Optional[int]=None):
        fees, memo, destination, send_amount = self._maybe_default(fees, memo, destination, send_amount)
        tx_infos = {
            "payin_address": destination,
            "payin_extra_id": memo.encode(),
            "refund_address": b"ra7Zr8ddy9tB88RaXL8B87YkqhEJG2vkAJ",
            "refund_extra_id": b"",
            "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
            "payout_extra_id": b"",
            "currency_from": "XRP",
            "currency_to": "ETH",
            "amount_to_provider": int.to_bytes(send_amount, length=8, byteorder='big'),
            "amount_to_wallet": b"\246\333t\233+\330\000",
        }
        self.perform_valid_exchange_tx(backend, exchange_navigation_helper, SubCommand.SWAP, tx_infos, fees)


# Valid swap test with default values
def test_ripple_swap_valid_1(backend, exchange_navigation_helper):
    performer = RippleValidSwapPerformer()
    performer.perform_valid_swap(backend, exchange_navigation_helper)
    performer.perform_ripple_tx(backend)


# Valid swap test with non default values
def test_ripple_swap_valid_2(backend, exchange_navigation_helper):
    fees = 10078
    memo = "123"
    destination = "rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4"
    send_amount = 446739662

    performer = RippleValidSwapPerformer()
    performer.perform_valid_swap(backend, exchange_navigation_helper, fees=fees, memo=memo, destination=destination, send_amount=send_amount)
    performer.perform_ripple_tx(backend, fees=fees, memo=memo, destination=destination, send_amount=send_amount)


# Make a valid swap and then ask a second signature
def test_ripple_swap_refuse_double_sign(backend, exchange_navigation_helper):
    performer = RippleValidSwapPerformer()
    performer.perform_valid_swap(backend, exchange_navigation_helper)
    performer.perform_ripple_tx(backend)

    with pytest.raises(ExceptionRAPDU) as e:
        performer.perform_ripple_tx(backend)
    assert e.value.status == Errors.WRONG_P2


# Test swap with a malicious Ripple TX with tampered fees
def test_ripple_swap_wrong_fees(backend, exchange_navigation_helper):
    performer = RippleValidSwapPerformer()
    performer.perform_valid_swap(backend, exchange_navigation_helper)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_ripple_tx(backend, fees=performer.def_fees + 100)
    assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# Test swap with a malicious Ripple TX with tampered memo
def test_ripple_swap_wrong_memo(backend, exchange_navigation_helper):
    performer = RippleValidSwapPerformer()
    performer.perform_valid_swap(backend, exchange_navigation_helper)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_ripple_tx(backend, memo=performer.def_memo + "1")
    assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# Test swap with a malicious Ripple TX with tampered dest
def test_ripple_swap_wrong_dest(backend, exchange_navigation_helper):
    performer = RippleValidSwapPerformer()
    performer.perform_valid_swap(backend, exchange_navigation_helper)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_ripple_tx(backend, destination="rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4")
    assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# Test swap with a malicious Ripple TX with tampered amount
def test_ripple_swap_wrong_amount(backend, exchange_navigation_helper):
    performer = RippleValidSwapPerformer()
    performer.perform_valid_swap(backend, exchange_navigation_helper)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_ripple_tx(backend, send_amount=performer.def_send_amount + 351)
    assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


##############
# FUND tests #
##############

# class RippleValidFundPerformer(RippleValidTxPerformer):
#     # Helper to send a valid FUND TX to the Exchange app, provide parameters to overload te default values
#     def perform_valid_fund(self,
#                            backend,
#                            navigator,
#                            test_name,
#                            fees: Optional[int]=None,
#                            memo: Optional[str]=None,
#                            destination: Optional[str]=None,
#                            send_amount: Optional[int]=None):
#         fees, memo, destination, send_amount = self._maybe_default(fees, memo, destination, send_amount)
#         tx_infos = {
#             "user_id": "Jon Wick",
#             "account_name": "My account 00",
#             "in_currency": "XRP",
#             "in_amount": int.to_bytes(send_amount, length=4, byteorder='big'),
#             "in_address": destination,
#         }
#         self.perform_valid_exchange_tx(backend, exchange_navigation_helper, SubCommand.FUND, tx_infos, fees)


# # Valid fund test with default values
# def test_ripple_fund_valid_1(backend, exchange_navigation_helper):
#     performer = RippleValidFundPerformer()
#     performer.perform_valid_fund(backend, exchange_navigation_helper)
#     performer.perform_ripple_tx(backend)


# # Valid fund test with non default values
# def test_ripple_fund_valid_2(backend, exchange_navigation_helper):
#     fees = 10078
#     destination="rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4"
#     send_amount = 446739662

#     performer = RippleValidFundPerformer()
#     performer.perform_valid_fund(backend, exchange_navigation_helper, fees=fees, destination=destination, send_amount=send_amount)
#     performer.perform_ripple_tx(backend, fees=fees, destination=destination, send_amount=send_amount)


# # Make a valid fund and then ask a second signature
# def test_ripple_fund_refuse_double_sign(backend, exchange_navigation_helper):
#     performer = RippleValidFundPerformer()
#     performer.perform_valid_fund(backend, exchange_navigation_helper)
#     performer.perform_ripple_tx(backend)

#     with pytest.raises(ExceptionRAPDU) as e:
#         performer.perform_ripple_tx(backend)
#     assert e.value.status == Errors.WRONG_P2


# # Test fund with a malicious Ripple TX with tampered fees
# def test_ripple_fund_wrong_fees(backend, exchange_navigation_helper):
#     performer = RippleValidFundPerformer()
#     performer.perform_valid_fund(backend, exchange_navigation_helper)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_ripple_tx(backend, fees=performer.def_fees + 100)
#     assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# # Test fund with a malicious Ripple TX with tampered memo
# def test_ripple_fund_wrong_memo(backend, exchange_navigation_helper):
#     performer = RippleValidFundPerformer()
#     performer.perform_valid_fund(backend, exchange_navigation_helper)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_ripple_tx(backend, memo=performer.def_memo + "1")
#     assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# # Test fund with a malicious Ripple TX with tampered dest
# def test_ripple_fund_wrong_dest(backend, exchange_navigation_helper):
#     performer = RippleValidFundPerformer()
#     performer.perform_valid_fund(backend, exchange_navigation_helper)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_ripple_tx(backend, destination="rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4")
#     assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# # Test fund with a malicious Ripple TX with tampered amount
# def test_ripple_fund_wrong_amount(backend, exchange_navigation_helper):
#     performer = RippleValidFundPerformer()
#     performer.perform_valid_fund(backend, exchange_navigation_helper)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_ripple_tx(backend, send_amount=performer.def_send_amount + 351)
#     assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# ##############
# # SELL tests #
# ##############

# class RippleValidSellPerformer(RippleValidTxPerformer):
#     # Helper to send a valid SELL TX to the Exchange app, provide parameters to overload te default values
#     def perform_valid_sell(self,
#                            backend,
#                            navigator,
#                            test_name,
#                            fees: Optional[int]=None,
#                            memo: Optional[str]=None,
#                            destination: Optional[str]=None,
#                            send_amount: Optional[int]=None):
#         fees, memo, destination, send_amount = self._maybe_default(fees, memo, destination, send_amount)
#         tx_infos = {
#             "trader_email": "john@doe.lost",
#             "out_currency": "USD",
#             "out_amount": {"coefficient": b"\x01", "exponent": 3},
#             "in_currency": "XRP",
#             "in_amount": int.to_bytes(send_amount, length=4, byteorder='big'),
#             "in_address": destination,
#         }
#         self.perform_valid_exchange_tx(backend, exchange_navigation_helper, SubCommand.SELL, tx_infos, fees)


# # Valid sell test with default values
# def test_ripple_sell_valid_1(backend, exchange_navigation_helper):
#     performer = RippleValidSellPerformer()
#     performer.perform_valid_sell(backend, exchange_navigation_helper)
#     performer.perform_ripple_tx(backend)


# # Valid sell test with non default values
# def test_ripple_sell_valid_2(backend, exchange_navigation_helper):
#     fees = 10078
#     destination="rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4"
#     send_amount = 446739662

#     performer = RippleValidSellPerformer()
#     performer.perform_valid_sell(backend, exchange_navigation_helper, fees=fees, destination=destination, send_amount=send_amount)
#     performer.perform_ripple_tx(backend, fees=fees, destination=destination, send_amount=send_amount)


# # Make a valid sell and then ask a second signature
# def test_ripple_sell_refuse_double_sign(backend, exchange_navigation_helper):
#     performer = RippleValidSellPerformer()
#     performer.perform_valid_sell(backend, exchange_navigation_helper)
#     performer.perform_ripple_tx(backend)

#     with pytest.raises(ExceptionRAPDU) as e:
#         performer.perform_ripple_tx(backend)
#     assert e.value.status == Errors.WRONG_P2


# # Test sell with a malicious Ripple TX with tampered fees
# def test_ripple_sell_wrong_fees(backend, exchange_navigation_helper):
#     performer = RippleValidSellPerformer()
#     performer.perform_valid_sell(backend, exchange_navigation_helper)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_ripple_tx(backend, fees=performer.def_fees + 100)
#     assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# # Test sell with a malicious Ripple TX with tampered memo
# def test_ripple_sell_wrong_memo(backend, exchange_navigation_helper):
#     performer = RippleValidSellPerformer()
#     performer.perform_valid_sell(backend, exchange_navigation_helper)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_ripple_tx(backend, memo=performer.def_memo + "1")
#     assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# # Test sell with a malicious Ripple TX with tampered dest
# def test_ripple_sell_wrong_dest(backend, exchange_navigation_helper):
#     performer = RippleValidSellPerformer()
#     performer.perform_valid_sell(backend, exchange_navigation_helper)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_ripple_tx(backend, destination="rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4")
#     assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL


# # Test sell with a malicious Ripple TX with tampered amount
# def test_ripple_sell_wrong_amount(backend, exchange_navigation_helper):
#     performer = RippleValidSellPerformer()
#     performer.perform_valid_sell(backend, exchange_navigation_helper)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_ripple_tx(backend, send_amount=performer.def_send_amount + 351)
#     assert rapdu.status == RippleErrors.SW_SWAP_CHECKING_FAIL
