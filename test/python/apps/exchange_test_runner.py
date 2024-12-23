import pytest
from typing import Optional, Tuple, List

from ragger.backend import RaisePolicy
from ragger.utils import RAPDU
from ragger.error import ExceptionRAPDU

from .exchange import ExchangeClient, Rate, SubCommand, Errors
from .exchange_transaction_builder import get_partner_curve, get_credentials, craft_and_sign_tx
from . import cal as cal
from .signing_authority import SigningAuthority, LEDGER_SIGNER

from ..utils import handle_lib_call_start_or_stop, int_to_minimally_sized_bytes

# When adding a new test, have it prefixed by this string in order to have it automatically parametrized for currencies tests
TEST_METHOD_PREFIX="perform_test_"

# Exchange tests helpers, create a child of this class that define coin-specific elements and call its tests entry points
class ExchangeTestRunner:

    # You will need to define the following elements in the child application:
    # currency_configuration: CurrencyConfiguration
    # valid_destination_1: str
    # valid_destination_2: str
    # valid_refund: str
    # valid_send_amount_1: int
    # valid_send_amount_2: int
    # valid_fees_1: int
    # valid_fees_2: int
    # fake_refund: str
    # fake_payout: str

    # Values to overwrite if your application uses memo
    valid_destination_memo_1: str = ""
    valid_destination_memo_2: str = ""
    valid_refund_memo: str = ""
    fake_refund_memo: str = ""
    fake_payout_memo: str = ""

    # Values to overwrite if your application supports extra_data
    valid_payin_extra_data_1: bytes = b""
    valid_payin_extra_data_2: bytes = b""
    invalid_payin_extra_data: bytes = b""

    # signature_refusal_error_code: int
    #
    # you can override signature_refusal_error_code with specific values
    # wrong_method_error_code: int
    # wrong_fees_error_code: int
    # wrong_memo_error_code: int
    # wrong_extra_data_error_code: int
    # wrong_destination_error_code: int
    # wrong_amount_error_code: int

    # You can optionally overwrite the following default values if you want
    partner_name = "Default name"
    fund_user_id = "Jon Wick"
    fund_account_name = "My account 00"
    sell_trader_email = "john@doe.lost"
    sell_out_currency = "USD"
    sell_out_amount = {"coefficient": b"\x01", "exponent": 3}

    signature_refusal_error_code = None
    wrong_method_error_code = None
    wrong_fees_error_code = None
    wrong_memo_error_code = None
    wrong_extra_data_error_code = None
    wrong_destination_error_code = None
    wrong_amount_error_code = None

    alias_address: Optional[bytes] = None
    _alias_refund_address: Optional[bytes] = None
    _alias_payout_address: Optional[bytes] = None

    def __init__(self, backend, exchange_navigation_helper):
        self.backend = backend
        self.exchange_navigation_helper = exchange_navigation_helper

        if self.wrong_method_error_code is None:
            self.wrong_method_error_code = self.signature_refusal_error_code
        if self.wrong_fees_error_code is None:
            self.wrong_fees_error_code = self.signature_refusal_error_code
        if self.wrong_memo_error_code is None:
            self.wrong_memo_error_code = self.signature_refusal_error_code
        if self.wrong_extra_data_error_code is None:
            self.wrong_extra_data_error_code = self.signature_refusal_error_code
        if self.wrong_destination_error_code is None:
            self.wrong_destination_error_code = self.signature_refusal_error_code
        if self.wrong_amount_error_code is None:
            self.wrong_amount_error_code = self.signature_refusal_error_code

    def run_test(self, function_to_test: str):
        # Remove the flow suffix as the function is the same and the snapshot path is the same too
        self.exchange_navigation_helper.set_test_name_suffix("_" + function_to_test)
        getattr(self, TEST_METHOD_PREFIX + function_to_test)()

    def _perform_valid_exchange(self, subcommand, tx_infos, from_currency_configuration, to_currency_configuration, fees, ui_validation):
        # Initialize the exchange client plugin that will format and send the APDUs to the device
        ex = ExchangeClient(self.backend, Rate.FIXED, subcommand)

        # The partner we will perform the exchange with
        partner = SigningAuthority(curve=get_partner_curve(subcommand), name=self.partner_name)

        # Initialize a new transaction request
        transaction_id = ex.init_transaction().data

        # Enroll the partner
        credentials = get_credentials(subcommand, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))

        # Craft the exchange transaction proposal and have it signed by the enrolled partner
        tx, tx_signature = craft_and_sign_tx(subcommand, tx_infos, transaction_id, fees, partner)

        # Send the exchange transaction proposal and its signature
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        # Ask our fake CAL the coin configuration for both FROM and TO currencies (None for TO in case of FUND or SELL)
        from_configuration = from_currency_configuration.get_conf_for_ticker()

        if subcommand == SubCommand.SWAP_NG:
            if self._alias_refund_address is not None:
                challenge = ex.get_challenge().data
                ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, trusted_name=tx_infos["refund_address"], address=self._alias_refund_address)
            if self._alias_payout_address is not None:
                challenge = ex.get_challenge().data
                ex.send_pki_certificate_and_trusted_name_descriptor(challenge=challenge, trusted_name=tx_infos["payout_address"], address=self._alias_payout_address)

            to_configuration = to_currency_configuration.get_conf_for_ticker()
            ex.check_payout_address(to_configuration)

            # Request the final address check and UI approval request on the device
            ex.check_refund_address_no_display(from_configuration)
        else:
            ex.check_asset_in_no_display(from_configuration)

        with ex.prompt_ui_display():
            if ui_validation:
                self.exchange_navigation_helper.simple_accept()
            else:
                # Calling the navigator delays the RAPDU reception until the end of navigation
                # Which is problematic if the RAPDU is an error as we would not raise until the navigation is done
                # As a workaround, we avoid calling the navigation if we want the function to raise
                pass

        self.exchange_navigation_helper.wait_for_exchange_spinner()

        # Ask exchange to start the library application to sign the actual outgoing transaction
        ex.start_signing_transaction()

        self.exchange_navigation_helper.wait_for_library_spinner()

    def perform_valid_swap_from_custom(self, destination, send_amount, fees, destination_memo, refund_address=None, refund_memo=None, ui_validation=True, allow_alias=True):
        # Refund data is almost always 'valid', make it optionnal to specify it
        refund_address = self.valid_refund if refund_address is None else refund_address
        refund_memo = self.valid_refund_memo if refund_memo is None else refund_memo
        tx_infos = {
            "payin_address": destination,
            "payin_extra_id": destination_memo,
            "refund_address": refund_address,
            "refund_extra_id": refund_memo,
            "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D", # Default
            "payout_extra_id": b"", # Default
            "currency_from": self.currency_configuration.ticker,
            "currency_to": cal.ETH_CURRENCY_CONFIGURATION.ticker,
            "amount_to_provider": int_to_minimally_sized_bytes(send_amount),
            "amount_to_wallet": b"\246\333t\233+\330\000", # Default
        }
        if allow_alias:
            self._alias_refund_address = self.alias_address
        self._perform_valid_exchange(SubCommand.SWAP_NG, tx_infos, self.currency_configuration, cal.ETH_CURRENCY_CONFIGURATION, fees, ui_validation=ui_validation)

    def perform_valid_thorswap_from_custom(self, destination, send_amount, fees, payin_extra_data, refund_address=None, ui_validation=True, allow_alias=True):
        refund_address = self.valid_refund if refund_address is None else refund_address
        tx_infos = {
            "payin_address": destination,
            "payin_extra_data": payin_extra_data,
            "refund_address": refund_address,
            "refund_extra_id": b"",
            "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D", # Default
            "payout_extra_id": b"",
            "currency_from": self.currency_configuration.ticker,
            "currency_to": cal.ETH_CURRENCY_CONFIGURATION.ticker,
            "amount_to_provider": int_to_minimally_sized_bytes(send_amount),
            "amount_to_wallet": b"\246\333t\233+\330\000", # Default
        }
        if allow_alias:
            self._alias_refund_address = self.alias_address
        self._perform_valid_exchange(SubCommand.SWAP_NG, tx_infos, self.currency_configuration, cal.ETH_CURRENCY_CONFIGURATION, fees, ui_validation=ui_validation)

    def perform_valid_swap_to_custom(self, destination, send_amount, fees, destination_memo, ui_validation=True, allow_alias=True):
        tx_infos = {
            "payin_address": "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D", # Default
            "payin_extra_id": "", # Default
            "refund_address": "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D", # Default
            "refund_extra_id": "", # Default
            "payout_address": destination,
            "payout_extra_id": destination_memo,
            "currency_from": cal.ETH_CURRENCY_CONFIGURATION.ticker,
            "currency_to": self.currency_configuration.ticker,
            "amount_to_provider": int_to_minimally_sized_bytes(send_amount),
            "amount_to_wallet": b"\246\333t\233+\330\000", # Default
        }
        if allow_alias:
            self._alias_payout_address = self.alias_address
        self._perform_valid_exchange(SubCommand.SWAP_NG, tx_infos, cal.ETH_CURRENCY_CONFIGURATION, self.currency_configuration, fees, ui_validation=ui_validation)

    def perform_valid_fund_from_custom(self, destination, send_amount, fees):
        tx_infos = {
            "user_id": self.fund_user_id,
            "account_name": self.fund_account_name,
            "in_currency": self.currency_configuration.ticker,
            "in_amount": int_to_minimally_sized_bytes(send_amount),
            "in_address": destination,
        }
        self._perform_valid_exchange(SubCommand.FUND_NG, tx_infos, self.currency_configuration, None, fees, ui_validation=True)

    def perform_valid_sell_from_custom(self, destination, send_amount, fees):
        tx_infos = {
            "trader_email": self.sell_trader_email,
            "out_currency": self.sell_out_currency,
            "out_amount": self.sell_out_amount,
            "in_currency": self.currency_configuration.ticker,
            "in_amount": int_to_minimally_sized_bytes(send_amount),
            "in_address": destination,
        }
        self._perform_valid_exchange(SubCommand.SELL_NG, tx_infos, self.currency_configuration, None, fees, ui_validation=True)

    # Implement this function for each tested coin
    def perform_final_tx(self, destination, send_amount, fees, memo):
        raise NotImplementedError

    # Wrapper of the function above to handle the USB reset in the parent class instead of the currency class
    def perform_coin_specific_final_tx(self, destination, send_amount, fees, memo):
        try:
            self.perform_final_tx(destination, send_amount, fees, memo)
        except Exception as e:
            raise e
        finally:
            self.exchange_navigation_helper.check_post_sign_display()
            handle_lib_call_start_or_stop(self.backend)

    def assert_exchange_is_started(self):
        # We don't care at all for the subcommand / rate
        ExchangeClient(self.backend, Rate.FIXED, SubCommand.SWAP_NG).assert_exchange_is_started()

    def skip_thorswap_if_needed(self):
        if self.backend.firmware.device == "nanos":
            pytest.skip("Thorswap is not implemented on NanoS device")

    #########################################################
    # Generic SWAP tests functions, call them in your tests #
    #########################################################

    # We test that the currency app returns a fail when checking an incorrect refund address
    def perform_test_swap_wrong_refund(self):
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_valid_swap_from_custom(self.valid_destination_1,
                                                self.valid_send_amount_1,
                                                self.valid_fees_1,
                                                self.valid_destination_memo_1,
                                                refund_address=self.fake_refund,
                                                refund_memo=self.fake_refund_memo,
                                                ui_validation=False,
                                                allow_alias=False)
        assert e.value.status == Errors.INVALID_ADDRESS

    # We test that the currency app returns a fail when checking an incorrect payout address
    def perform_test_swap_wrong_payout(self):
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_valid_swap_to_custom(self.fake_payout,
                                              self.valid_send_amount_1,
                                              self.valid_fees_1,
                                              self.fake_payout_memo,
                                              ui_validation=False,
                                              allow_alias=False)
        assert e.value.status == Errors.INVALID_ADDRESS

    # The absolute standard swap, using default values, user accepts on UI
    def perform_test_swap_valid_1(self):
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        self.assert_exchange_is_started()

    # The second standard swap, using alternate default values, user accepts on UI
    def perform_test_swap_valid_2(self):
        self.perform_valid_swap_from_custom(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, self.valid_destination_memo_2)
        self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, self.valid_destination_memo_2)
        self.assert_exchange_is_started()

    # Test swap with a malicious TX with tampered fees
    def perform_test_swap_wrong_fees(self):
        assert self.valid_fees_1 != self.valid_fees_2, "This test won't work if the values are the same"
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_2, self.valid_destination_memo_1)
        assert e.value.status == self.wrong_fees_error_code
        self.assert_exchange_is_started()

    # Test swap with a malicious TX with tampered memo
    def perform_test_swap_wrong_memo(self):
        if self.valid_destination_memo_1 == self.valid_destination_memo_2:
            pytest.skip("This test won't work if the values are the same")
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_2)
        assert e.value.status == self.wrong_memo_error_code
        self.assert_exchange_is_started()

    # Test swap with a malicious TX with tampered destination
    def perform_test_swap_wrong_destination(self):
        assert self.valid_destination_1 != self.valid_destination_2, "This test won't work if the values are the same"
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        assert e.value.status == self.wrong_destination_error_code
        self.assert_exchange_is_started()

    # Test swap with a malicious TX with tampered amount
    def perform_test_swap_wrong_amount(self):
        assert self.valid_send_amount_1 != self.valid_send_amount_2, "This test won't work if the values are the same"
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_destination_memo_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_2, self.valid_fees_1, self.valid_destination_memo_1)
        assert e.value.status == self.wrong_amount_error_code
        self.assert_exchange_is_started()

    #######################################################################
    # Thorswap / LiFi / ... SWAP tests functions, call them in your tests #
    #######################################################################

    def perform_test_thorswap_valid_1(self):
        self.skip_thorswap_if_needed()
        self.perform_valid_thorswap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_payin_extra_data_1)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_payin_extra_data_1)
        self.assert_exchange_is_started()

    def perform_test_thorswap_valid_2(self):
        self.skip_thorswap_if_needed()
        self.perform_valid_thorswap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_payin_extra_data_2)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_payin_extra_data_2)
        self.assert_exchange_is_started()

    def perform_test_thorswap_wrong_hash(self):
        self.skip_thorswap_if_needed()
        self.perform_valid_thorswap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_payin_extra_data_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_payin_extra_data_2)
        assert e.value.status == self.wrong_extra_data_error_code
        self.assert_exchange_is_started()

    def perform_test_thorswap_invalid_type(self):
        self.skip_thorswap_if_needed()
        self.perform_valid_thorswap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.invalid_payin_extra_data)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.invalid_payin_extra_data)
        assert e.value.status == self.wrong_extra_data_error_code
        self.assert_exchange_is_started()

    def perform_test_thorswap_unexpected_extra_data(self):
        self.skip_thorswap_if_needed()
        self.perform_valid_swap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "")
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_payin_extra_data_1)
        assert e.value.status == self.wrong_extra_data_error_code
        self.assert_exchange_is_started()

    def perform_test_thorswap_missing_extra_data(self):
        self.skip_thorswap_if_needed()
        self.perform_valid_thorswap_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, self.valid_payin_extra_data_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, None)
        assert e.value.status == self.wrong_extra_data_error_code
        self.assert_exchange_is_started()

    #########################################################
    # Generic FUND tests functions, call them in your tests #
    #########################################################

    # The absolute standard fund, using default values, user accepts on UI
    def perform_test_fund_valid_1(self):
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "")
        self.assert_exchange_is_started()

    # The second standard fund, using alternate default values, user accepts on UI
    def perform_test_fund_valid_2(self):
        self.perform_valid_fund_from_custom(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2)
        self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, "")
        self.assert_exchange_is_started()

    # Test fund with a malicious TX with tampered fees
    def perform_test_fund_wrong_fees(self):
        assert self.valid_fees_1 != self.valid_fees_2, "This test won't work if the values are the same"
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_2, "")
        assert e.value.status == self.wrong_fees_error_code
        self.assert_exchange_is_started()

    # Test fund with a malicious TX with tampered memo
    def perform_test_fund_wrong_memo(self):
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "no memo expected")
        assert e.value.status == self.wrong_memo_error_code
        self.assert_exchange_is_started()

    # Test fund with a malicious TX with tampered destination
    def perform_test_fund_wrong_destination(self):
        assert self.valid_destination_1 != self.valid_destination_2, "This test won't work if the values are the same"
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_1, self.valid_fees_1, "")
        assert e.value.status == self.wrong_destination_error_code
        self.assert_exchange_is_started()

    # Test fund with a malicious TX with tampered amount
    def perform_test_fund_wrong_amount(self):
        assert self.valid_send_amount_1 != self.valid_send_amount_2, "This test won't work if the values are the same"
        self.perform_valid_fund_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_2, self.valid_fees_1, "")
        assert e.value.status == self.wrong_amount_error_code
        self.assert_exchange_is_started()

    #########################################################
    # Generic SELL tests functions, call them in your tests #
    #########################################################

    # The absolute standard sell, using default values, user accepts on UI
    def perform_test_sell_valid_1(self):
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "")
        self.assert_exchange_is_started()

    # The second standard sell, using alternate default values, user accepts on UI
    def perform_test_sell_valid_2(self):
        self.perform_valid_sell_from_custom(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2)
        self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_2, self.valid_fees_2, "")
        self.assert_exchange_is_started()

    # Test sell with a malicious TX with tampered fees
    def perform_test_sell_wrong_fees(self):
        assert self.valid_fees_1 != self.valid_fees_2, "This test won't work if the values are the same"
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_2, "")
        assert e.value.status == self.wrong_fees_error_code
        self.assert_exchange_is_started()

    # Test sell with a malicious TX with tampered memo
    def perform_test_sell_wrong_memo(self):
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1, "no memo expected")
        assert e.value.status == self.wrong_memo_error_code
        self.assert_exchange_is_started()

    # Test sell with a malicious TX with tampered destination
    def perform_test_sell_wrong_destination(self):
        assert self.valid_destination_1 != self.valid_destination_2, "This test won't work if the values are the same"
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_2, self.valid_send_amount_1, self.valid_fees_1, "")
        assert e.value.status == self.wrong_destination_error_code
        self.assert_exchange_is_started()

    # Test sell with a malicious TX with tampered amount
    def perform_test_sell_wrong_amount(self):
        assert self.valid_send_amount_1 != self.valid_send_amount_2, "This test won't work if the values are the same"
        self.perform_valid_sell_from_custom(self.valid_destination_1, self.valid_send_amount_1, self.valid_fees_1)
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1, self.valid_send_amount_2, self.valid_fees_1, "")
        assert e.value.status == self.wrong_amount_error_code
        self.assert_exchange_is_started()

# Automatically collect all tests functions and export their name in ready-to-be-parametrized lists
_all_test_methods_prefixed = [method for method in dir(ExchangeTestRunner) if method.startswith(TEST_METHOD_PREFIX)]
# Remove prefix to have nice snapshots directories
ALL_TESTS = [str(i).replace(TEST_METHOD_PREFIX, '') for i in _all_test_methods_prefixed]
ALL_TESTS_EXCEPT_MEMO = [test for test in ALL_TESTS if not "memo" in test]
ALL_TESTS_EXCEPT_THORSWAP = [test for test in ALL_TESTS if not "thorswap" in test]
ALL_TESTS_EXCEPT_FEES = [test for test in ALL_TESTS if not "fees" in test]
SWAP_TESTS = [test for test in ALL_TESTS if "swap" in test]
FUND_TESTS = [test for test in ALL_TESTS if "fund" in test]
SELL_TESTS = [test for test in ALL_TESTS if "sell" in test]
VALID_TESTS = [test for test in ALL_TESTS if "valid" in test]

def common_part(a, b) -> List:
    a_set = set(a)
    b_set = set(b)

    # check length
    if len(a_set.intersection(b_set)) > 0:
        return list(a_set.intersection(b_set))
    else:
        return []


ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP = common_part(ALL_TESTS_EXCEPT_MEMO, ALL_TESTS_EXCEPT_THORSWAP)
ALL_TESTS_EXCEPT_MEMO_AND_FEES = common_part(ALL_TESTS_EXCEPT_MEMO, ALL_TESTS_EXCEPT_FEES)
ALL_TESTS_EXCEPT_THORSWAP_AND_FEES = common_part(ALL_TESTS_EXCEPT_THORSWAP, ALL_TESTS_EXCEPT_FEES)
ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES = common_part(ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP, ALL_TESTS_EXCEPT_FEES)
SWAP_TESTS_EXCEPT_THORSWAP = common_part(SWAP_TESTS, ALL_TESTS_EXCEPT_THORSWAP)
VALID_TESTS_EXCEPT_THORSWAP = common_part(VALID_TESTS, ALL_TESTS_EXCEPT_THORSWAP)
