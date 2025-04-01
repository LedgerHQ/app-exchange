# --8<-- [start:native_test]
import pytest
import os

from .apps.ton_application_client.ton_transaction import Transaction, SendMode, CommentPayload, Payload, JettonTransferPayload, NFTTransferPayload, CustomUnsafePayload, JettonBurnPayload, AddWhitelistPayload, SingleNominatorWithdrawPayload, ChangeValidatorPayload, TonstakersDepositPayload, JettonDAOVotePayload, ChangeDNSWalletPayload, ChangeDNSPayload, TokenBridgePaySwapPayload
from .apps.ton_application_client.ton_command_sender import BoilerplateCommandSender, Errors
from .apps.ton_application_client.ton_response_unpacker import unpack_sign_tx_response
from .apps.ton_utils import check_signature_validity

from tonsdk.utils import Address

from .apps.exchange_test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES
from .apps.ton import DEVICE_PUBLIC_KEY, Bounceability, WorkchainID, craft_address, SW_SWAP_FAILURE, TON_DERIVATION_PATH
from .apps import cal as cal


# ExchangeTestRunner implementation for Ton
class TonTests(ExchangeTestRunner):
    # The coin configuration used for this currency
    currency_configuration = cal.TON_CURRENCY_CONFIGURATION

    # A valid TON address that will be used as trade partner address in the tests
    valid_destination_1 = "EQD0sKn8DbS12U015TWOSpYmyJYYDC_7sxg1upaMxnBvTiX8"
    # A different one with the same purpose
    valid_destination_2 = "EQANxfGN1EgFPawYB1fhPqebKe1Nb6FIsaiekEecJ6R-3kYF"

    # The address of the device with the Speculos seed on the derivation path used in
    # self.currency_configuration
    valid_refund = "UQDWey_FGPhd3phmerdVXi-zUIujfyO4-29y_VT1yD0meY1n"

    # Amounts that will be used by the trade partner in this tests
    valid_send_amount_1 = 12345670000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100000000
    valid_fees_2 = 10000123

    # An address that is not the address of the device with the Speculos seed on the derivation
    # path used in self.currency_configuration.
    fake_refund = "EQD0sKn8DbS12U015TWOSpYmyJYYDC_7sxg1upaMxnBvTiX8"
    fake_payout = "EQD0sKn8DbS12U015TWOSpYmyJYYDC_7sxg1upaMxnBvTiX8"

    # The error code returned by the application when refusing to validate the final transaction.
    wrong_method_error_code = SW_SWAP_FAILURE
    wrong_destination_error_code = SW_SWAP_FAILURE
    wrong_amount_error_code = SW_SWAP_FAILURE

    # The perform_final_tx() function will be called by the ExchangeTestRunner class to finalize a
    # TON payment if needed by the test.
    # This function will create a TON payment of 'send_amount' with 'fees' to 'destination'
    def perform_final_tx(self, destination, send_amount, fees, memo):
        # Unused memo

        # Use the app interface instead of raw interface
        client = BoilerplateCommandSender(self.backend)

        # First we need to get the public key of the device in order to build the transaction
        pubkey = client.get_public_key(path=TON_DERIVATION_PATH).data

        # Create the transaction that will be sent to the device for signing
        tx = Transaction(Address(destination),
                         SendMode.PAY_GAS_SEPARATLY,
                         0,
                         1686176000,
                         True,
                         send_amount)
        tx_bytes = tx.to_request_bytes()

        # Send the sign device instruction.
        with client.sign_tx(path=TON_DERIVATION_PATH, transaction=tx_bytes):
            # As there is no display inside the TON call when using the application through
            # Exchange, we simply end the asynchronism.
            pass

        # The device as yielded the result, parse it and ensure that the signature is correct
        response = client.get_async_response().data
        sig, hash_b = unpack_sign_tx_response(response)
        assert hash_b == tx.transfer_cell().bytes_hash()
        assert check_signature_validity(pubkey, sig, hash_b)


# Use a class to reuse the same Speculos instance
class TestsTon:

    # Paremetrize the test_ton function with all the ExchangeTestRunner tests to run
    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
    def test_ton(self, backend, exchange_navigation_helper, test_to_run):
        if backend.firmware.device == "nanos":
            pytest.skip("TON swap is not supported on NanoS device")

        # Forward to the ExchangeTestRunner the parametrized test to run
        TonTests(backend, exchange_navigation_helper).run_test(test_to_run)
# --8<-- [end:native_test]

# class TonUSDTTests(TonTests):
#     currency_configuration = cal.TON_CURRENCY_CONFIGURATION
#     def perform_final_tx(self, destination, send_amount, fees, memo):
#         # Use the app interface instead of raw interface
#         client = BoilerplateCommandSender(self.backend)

#         # First we need to get the public key of the device in order to build the transaction
#         pubkey = client.get_public_key(path=TON_DERIVATION_PATH).data

#         payload = JettonTransferPayload(100, Address("0:" + "0" * 64), forward_amount=1)

#         tx = Transaction(Address("0:" + "0" * 64), SendMode.PAY_GAS_SEPARATLY, 0, 1686176000, True, 100000000, payload=payload)
#         tx_bytes = tx.to_request_bytes()

#         with client.sign_tx(path=TON_DERIVATION_PATH, transaction=tx_bytes):
#             pass

#         # The device as yielded the result, parse it and ensure that the signature is correct
#         response = client.get_async_response().data
#         sig, hash_b = unpack_sign_tx_response(response)
#         assert hash_b == tx.transfer_cell().bytes_hash()
#         assert check_signature_validity(pubkey, sig, hash_b)

# class TestsTonUSDT:
#     @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
#     def test_ton_usdt(self, backend, exchange_navigation_helper, test_to_run):
#         TonUSDTTests(backend, exchange_navigation_helper).run_test(test_to_run)
