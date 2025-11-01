import pytest
from ledger_app_clients.exchange.test_runner  import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES
from .apps import cal as cal

from .apps.kaspa import KAS_PATH, check_signature_validity
from .apps.kaspa_application_client.kaspa_command_sender import KaspaCommandSender, Errors as KaspaErrors, InsType, P1, P2
from .apps.kaspa_application_client.kaspa_response_unpacker import unpack_get_public_key_response, unpack_sign_tx_response
from .apps.kaspa_application_client.kaspa_transaction import Transaction, TransactionInput, TransactionOutput

# ExchangeTestRunner implementation for Near
class KaspaTests(ExchangeTestRunner):

    currency_configuration = cal.KAS_CURRENCY_CONFIGURATION
    valid_destination_1 = "kaspa:qrazhptjkcvrv23xz2xm8z8sfmg6jhxvmrscn7wph4k9we5tzxedwfxf0v6f8"
    valid_destination_memo_1 = ""
    valid_destination_2 = "kaspa:precqv0krj3r6uyyfa36ga7s0u9jct0v4wg8ctsfde2gkrsgwgw8jgxfzfc98"
    valid_destination_memo_2 = ""
    valid_refund = "kaspa:qqhpcp4zd26y6wcdsqt3s8dk2zwd37cvdx2x4yv059fyc7cmuw9dgz5gl4tav"
    valid_refund_memo = ""
    valid_send_amount_1 = 543210000
    valid_send_amount_2 = 679000000123
    valid_fees_1 = 2036
    valid_fees_2 = 1111222233
    fake_refund = "abcdabcd"
    fake_refund_memo = "bla"
    fake_payout = "abcdabcd"
    fake_payout_memo = "bla"
    signature_refusal_error_code = KaspaErrors.SW_DENY
    wrong_amount_error_code = KaspaErrors.SW_WRONG_AMOUNT
    wrong_destination_error_code = KaspaErrors.SW_WRONG_ADDRESS

    def perform_final_tx(self, destination, send_amount, fees, memo):
        client = KaspaCommandSender(self.backend)

        path: str = KAS_PATH

        # First we need to get the public key of the device in order to build the transaction
        rapdu = client.get_public_key(path=path)
        _, public_key, _, _ = unpack_get_public_key_response(rapdu.data)

        # SPK for address: kaspa:qrazhptjkcvrv23xz2xm8z8sfmg6jhxvmrscn7wph4k9we5tzxedwfxf0v6f8
        script_public_key = "20fa2b8572b618362a26128db388f04ed1a95cccd8e189f9c1bd6c57668b11b2d7ac"
        if destination == "kaspa:precqv0krj3r6uyyfa36ga7s0u9jct0v4wg8ctsfde2gkrsgwgw8jgxfzfc98":
            script_public_key = "aa20f38031f61ca23d70844f63a477d07f0b2c2decab907c2e096e548b0e08721c7987"

        # Create the transaction that will be sent to the device for signing
        tx = Transaction(
            version=0,
            inputs=[
                TransactionInput(
                    value=send_amount + fees,
                    tx_id="40b022362f1a303518e2b49f86f87a317c87b514ca0f3d08ad2e7cf49d08cc70",
                    address_type=0,
                    address_index=0,
                    index=0,
                    public_key=public_key[1:33]
                )
            ],
            outputs=[
                TransactionOutput(
                    value=send_amount,
                    script_public_key=script_public_key
                )
            ]
        )

        with client.sign_tx(transaction=tx):
            pass

        idx = 0
        response = client.get_async_response().data
        has_more, input_index, _, der_sig, _, sighash = unpack_sign_tx_response(response)
        assert tx.get_sighash(input_index) == sighash
        assert check_signature_validity(public_key, der_sig, sighash)

        while has_more > 0:
            idx = idx + 1

            if idx > len(tx.inputs):
                break

            response = client.get_next_signature().data
            has_more, input_index, _, der_sig, _, sighash = unpack_sign_tx_response(response)
            assert tx.get_sighash(input_index) == sighash
            assert check_signature_validity(public_key, der_sig, sighash)


# Use a class to reuse the same Speculos instance
class TestsKaspa:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_THORSWAP_AND_FEES)
    def test_kaspa(self, backend, exchange_navigation_helper, test_to_run):
        KaspaTests(backend, exchange_navigation_helper).run_test(test_to_run)