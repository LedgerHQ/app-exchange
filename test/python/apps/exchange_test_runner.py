import pytest
from typing import Optional, Tuple

from ragger.backend import RaisePolicy
from ragger.utils import RAPDU
from ragger.error import ExceptionRAPDU

from .exchange import ExchangeClient, Rate, SubCommand, Errors
from .exchange_transaction_builder import get_partner_curve, craft_tx, encode_tx, extract_payout_ticker, extract_refund_ticker
from . import cal as cal
from .signing_authority import SigningAuthority, LEDGER_SIGNER

from ..utils import handle_lib_call_start_or_stop, int_to_minimally_sized_bytes

# When adding a new test, have it prefixed by this string in order to have it automatically parametrized for currencies tests
TEST_METHOD_PREFIX="perform_test_"
TEST_LEGACY_SUFFIX="_legacy_flow"
TEST_UNIFIED_SUFFIX="_ng_flow"

# Exchange tests helpers, create a child of this class that define coin-specific elements and call its tests entry points
class ExchangeTestRunner:

    # You will need to define the following elements in the child application:
    # currency_ticker: str
    # valid_destination_1: str
    # valid_destination_memo_1: str
    # valid_destination_2: str
    # valid_destination_memo_2: str
    # valid_refund: str
    # valid_refund_memo: str
    # valid_send_amount_1: int
    # valid_send_amount_2: int
    # valid_fees_1: int
    # valid_fees_2: int
    # fake_refund: str
    # fake_refund_memo: str
    # fake_payout: str
    # fake_payout_memo: str
    # signature_refusal_error_code: int

    # You can optionnaly overwrite the following default values if you want
    partner_name = "Default name"
    fund_user_id = "Jon Wick"
    fund_account_name = "My account 00"
    sell_trader_email = "john@doe.lost"
    sell_out_currency = "USD"
    sell_out_amount = {"coefficient": b"\x01", "exponent": 3}

    def __init__(self, backend, exchange_navigation_helper):
        self.backend = backend
        self.exchange_navigation_helper = exchange_navigation_helper

    def run_test(self, function_to_test: str):
        # Remove the flow suffix as the function is the same and the snapshot path is the same too
        if function_to_test.endswith(TEST_LEGACY_SUFFIX):
            use_legacy_flow = True
            function_to_test = function_to_test.removesuffix(TEST_LEGACY_SUFFIX)
        if function_to_test.endswith(TEST_UNIFIED_SUFFIX):
            use_legacy_flow = False
            function_to_test = function_to_test.removesuffix(TEST_UNIFIED_SUFFIX)
        self.exchange_navigation_helper.set_test_name_suffix("_" + function_to_test)
        getattr(self, TEST_METHOD_PREFIX + function_to_test)(use_legacy_flow)

    def _perform_valid_exchange(self, subcommand, tx_infos, fees, ui_validation):
        # Initialize the exchange client plugin that will format and send the APDUs to the device
        ex = ExchangeClient(self.backend, Rate.FIXED, subcommand)

        # The partner we will perform the exchange with
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name=self.partner_name)

        # Initialize a new transaction request
        transaction_id = ex.init_transaction().data

        # Enroll the partner
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

        # Craft the exchange transaction proposal and have it signed by the enrolled partner
        tx = craft_tx(subcommand, tx_infos, transaction_id)
        signed_tx = encode_tx(subcommand, partner, tx)

        # Send the exchange transaction proposal and it's signature
        ex.process_transaction(tx, fees)
        ex.check_transaction_signature(signed_tx)

        # Ask our fake CAL the coin configuration for both payout and refund tickers (None for refund in case of FUND or SELL)
        payout_ticker = extract_payout_ticker(subcommand, tx_infos)
        refund_ticker = extract_refund_ticker(subcommand, tx_infos)
        payout_configuration = cal.get_conf_for_ticker(payout_ticker)
        refund_configuration = cal.get_conf_for_ticker(refund_ticker)

        # Request the final address check and UI approval request on the device
        with ex.check_address(payout_configuration, refund_configuration):
            if ui_validation:
                self.exchange_navigation_helper.simple_accept()
            else:
                # Calling the navigator delays the RAPDU reception until the end of navigation
                # Which is problematic if the RAPDU is an error as we would not raise until the navigation is done
                # As a workaround, we avoid calling the navigation if we want the function to raise
                pass

        # Ask exchange to start the library application to sign the actual outgoing transaction
        ex.start_signing_transaction()

    def perform_valid_swap_from_custom(self, destination, send_amount, fees, memo, refund_address=None, refund_memo=None, ui_validation=True, legacy=False):
        refund_address = self.valid_refund if refund_address is None else refund_address
        refund_memo = self.valid_refund_memo if refund_memo is None else refund_memo
        tx_infos = {
            "payin_address": destination,
            "payin_extra_id": memo,
            "refund_address": refund_address,
            "refund_extra_id": refund_memo.encode(),
            "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D", # Default
            "payout_extra_id": b"", # Default
            "currency_from": self.currency_ticker,
            "currency_to": "ETH", # Default
            "amount_to_provider": int_to_minimally_sized_bytes(send_amount),
            "amount_to_wallet": b"\246\333t\233+\330\000", # Default
        }
        subcommand = SubCommand.SWAP if legacy else SubCommand.SWAP_NG
        self._perform_valid_exchange(subcommand, tx_infos, fees, ui_validation=ui_validation)

    def perform_valid_swap_to_custom(self, destination, send_amount, fees, memo, ui_validation=True, legacy=False):
        tx_infos = {
            "payin_address": "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D", # Default
            "payin_extra_id": "", # Default
            "refund_address": "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D", # Default
            "refund_extra_id": "", # Default
            "payout_address": destination,
            "payout_extra_id": memo.encode(),
            "currency_from": "ETH", # Default
            "currency_to": self.currency_ticker,
            "amount_to_provider": int_to_minimally_sized_bytes(send_amount),
            "amount_to_wallet": b"\246\333t\233+\330\000", # Default
        }
        subcommand = SubCommand.SWAP if legacy else SubCommand.SWAP_NG
        self._perform_valid_exchange(subcommand, tx_infos, fees, ui_validation=ui_validation)

    def perform_valid_fund_from_custom(self, destination, send_amount, fees, legacy=False):
        tx_infos = {
            "user_id": self.fund_user_id,
            "account_name": self.fund_account_name,
            "in_currency": self.currency_ticker,
            "in_amount": int_to_minimally_sized_bytes(send_amount),
            "in_address": destination,
        }
        subcommand = SubCommand.FUND if legacy else SubCommand.FUND_NG
        self._perform_valid_exchange(subcommand, tx_infos, fees, ui_validation=True)

    def perform_valid_sell_from_custom(self, destination, send_amount, fees, legacy=False):
        tx_infos = {
            "trader_email": self.sell_trader_email,
            "out_currency": self.sell_out_currency,
            "out_amount": self.sell_out_amount,
            "in_currency": self.currency_ticker,
            "in_amount": int_to_minimally_sized_bytes(send_amount),
            "in_address": destination,
        }
        subcommand = SubCommand.SELL if legacy else SubCommand.SELL_NG
        self._perform_valid_exchange(subcommand, tx_infos, fees, ui_validation=True)

    # Implement this function for each tested coin
    def perform_final_tx(self, destination, send_amount, fees, memo):
        raise NotImplementedError

    # Wrapper of the function above to handle the USB reset in the parent class instead of the currency class
    def perform_coin_specific_final_tx(self, destination, send_amount, fees, memo):
        self.perform_final_tx(destination, send_amount, fees, memo)
        handle_lib_call_start_or_stop(self.backend)

    #########################################################
    # Generic SWAP tests functions, call them in your tests #
    #########################################################

    # We test that the currency app returns a fail when checking an incorrect refund address
    def perform_test_swap_wrong_refund(self, legacy):
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_valid_swap_from_custom(self.valid_destination_1,
                                                self.valid_send_amount_1,
                                                self.valid_fees_1,
                                                self.valid_destination_memo_1,
                                                refund_address=self.fake_refund,
                                                refund_memo=self.fake_refund_memo,
                                                ui_validation=False,
                                                legacy=legacy)
        assert e.value.status == Errors.INVALID_ADDRESS

    # We test that the currency app returns a fail when checking an incorrect payout address
    def perform_test_swap_wrong_payout(self, legacy):
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_valid_swap_to_custom(self.fake_payout, self.valid_send_amount_1, self.valid_fees_1, self.fake_payout_memo, ui_validation=False, legacy=legacy)
        assert e.value.status == Errors.INVALID_ADDRESS

    # The absolute standard swap, using default values, user accepts on UI
    def perform_test_swap_valid_1(self, legacy):
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1, legacy=legacy)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)

    # The second standard swap, using alternate default values, user accepts on UI
    def perform_test_swap_valid_2(self, legacy):
        self.perform_valid_swap_from_custom(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, self.valid_destination_memo_2, legacy=legacy)
        self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, self.valid_destination_memo_2)

    # Make a valid swap and then ask a second signature
    def perform_test_swap_refuse_double_sign(self, legacy):
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1, legacy=legacy)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        assert e.value.status != 0x9000

    # Test swap with a malicious TX with tampered fees
    def perform_test_swap_wrong_fees(self, legacy):
        assert self.valid_fees_1 != self.valid_fees_2, "This test won't work if the values are the same"
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_2, self.valid_destination_memo_1)
        assert e.value.status == self.signature_refusal_error_code

    # Test swap with a malicious TX with tampered memo
    def perform_test_swap_wrong_memo(self, legacy):
        assert self.valid_destination_memo_1 != self.valid_destination_memo_2, "This test won't work if the values are the same"
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_2)
        assert e.value.status == self.signature_refusal_error_code

    # Test swap with a malicious TX with tampered destination
    def perform_test_swap_wrong_destination(self, legacy):
        assert self.valid_destination_1 != self.valid_destination_2, "This test won't work if the values are the same"
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        assert e.value.status == self.signature_refusal_error_code

    # Test swap with a malicious TX with tampered amount
    def perform_test_swap_wrong_amount(self, legacy):
        assert self.valid_send_amount_1 != self.valid_send_amount_2, "This test won't work if the values are the same"
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_2, self.valid_fees_1, self.valid_destination_memo_1)
        assert e.value.status == self.signature_refusal_error_code

    #########################################################
    # Generic FUND tests functions, call them in your tests #
    #########################################################

    # The absolute standard fund, using default values, user accepts on UI
    def perform_test_fund_valid_1(self, legacy):
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "")

    # The second standard fund, using alternate default values, user accepts on UI
    def perform_test_fund_valid_2(self, legacy):
        self.perform_valid_fund_from_custom(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, legacy=legacy)
        self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, "")

    # Make a valid fund and then ask a second signature
    def perform_test_fund_refuse_double_sign(self, legacy):
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "")
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "")
        assert e.value.status != 0x9000

    # Test fund with a malicious TX with tampered fees
    def perform_test_fund_wrong_fees(self, legacy):
        assert self.valid_fees_1 != self.valid_fees_2, "This test won't work if the values are the same"
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_2, "")
        assert e.value.status == self.signature_refusal_error_code

    # Test fund with a malicious TX with tampered memo
    def perform_test_fund_wrong_memo(self, legacy):
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "no memo expected")
        assert e.value.status == self.signature_refusal_error_code

    # Test fund with a malicious TX with tampered destination
    def perform_test_fund_wrong_destination(self, legacy):
        assert self.valid_destination_1 != self.valid_destination_2, "This test won't work if the values are the same"
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_1, self.valid_fees_1, "")
        assert e.value.status == self.signature_refusal_error_code

    # Test fund with a malicious TX with tampered amount
    def perform_test_fund_wrong_amount(self, legacy):
        assert self.valid_send_amount_1 != self.valid_send_amount_2, "This test won't work if the values are the same"
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_2, self.valid_fees_1, "")
        assert e.value.status == self.signature_refusal_error_code

    #########################################################
    # Generic SELL tests functions, call them in your tests #
    #########################################################

    # The absolute standard sell, using default values, user accepts on UI
    def perform_test_sell_valid_1(self, legacy):
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "")

    # The second standard sell, using alternate default values, user accepts on UI
    def perform_test_sell_valid_2(self, legacy):
        self.perform_valid_sell_from_custom(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, legacy=legacy)
        self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, "")

    # Make a valid sell and then ask a second signature
    def perform_test_sell_refuse_double_sign(self, legacy):
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "")
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "")
        assert e.value.status != 0x9000

    # Test sell with a malicious TX with tampered fees
    def perform_test_sell_wrong_fees(self, legacy):
        assert self.valid_fees_1 != self.valid_fees_2, "This test won't work if the values are the same"
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_2, "")
        assert e.value.status == self.signature_refusal_error_code

    # Test sell with a malicious TX with tampered memo
    def perform_test_sell_wrong_memo(self, legacy):
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "no memo expected")
        assert e.value.status == self.signature_refusal_error_code

    # Test sell with a malicious TX with tampered destination
    def perform_test_sell_wrong_destination(self, legacy):
        assert self.valid_destination_1 != self.valid_destination_2, "This test won't work if the values are the same"
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_1, self.valid_fees_1, "")
        assert e.value.status == self.signature_refusal_error_code

    # Test sell with a malicious TX with tampered amount
    def perform_test_sell_wrong_amount(self, legacy):
        assert self.valid_send_amount_1 != self.valid_send_amount_2, "This test won't work if the values are the same"
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, legacy=legacy)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_2, self.valid_fees_1, "")
        assert e.value.status == self.signature_refusal_error_code

# Automatically collect all tests functions and export their name in ready-to-be-parametrized lists
_all_test_methods_prefixed = [method for method in dir(ExchangeTestRunner) if method.startswith(TEST_METHOD_PREFIX)]
# Remove prefix to have nice snapshots directories
ALL_TESTS_NAME = [str(i).replace(TEST_METHOD_PREFIX, '') for i in _all_test_methods_prefixed]

# Parametrize with NG too
ALL_TESTS = [x + suffix for x in ALL_TESTS_NAME for suffix in (TEST_LEGACY_SUFFIX, TEST_UNIFIED_SUFFIX)]

ALL_TESTS_EXCEPT_MEMO = [test for test in ALL_TESTS if not "memo" in test]
ALL_TESTS_EXCEPT_MEMO_AND_FEES = [test for test in ALL_TESTS if (not "memo" in test and not "fees" in test)]
SWAP_TESTS = [test for test in ALL_TESTS if "swap" in test]
FUND_TESTS = [test for test in ALL_TESTS if "fund" in test]
SELL_TESTS = [test for test in ALL_TESTS if "sell" in test]
