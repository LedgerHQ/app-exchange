import pytest

from ragger.error import ExceptionRAPDU

from exchange_client.client import ExchangeClient, Rate, SubCommand, Errors
from exchange_client.transaction_builder import get_partner_curve, get_credentials, craft_and_sign_tx
from exchange_client.signing_authority import SigningAuthority, LEDGER_SIGNER
from apps import cal


class TestSellOutAmountOverflow:
    """Tests that incorrect out_amount values in SELL flows are properly rejected.
    """

    def _perform_sell_up_to_check_asset(self, backend, out_amount):
        """Run the SELL flow up to check_asset_in_no_display where format_fiat_amount is called."""
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SELL_NG)
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SELL_NG), name="Default name")

        transaction_id = ex.init_transaction().data

        credentials = get_credentials(SubCommand.SELL_NG, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))

        tx_infos = {
            "trader_email": "john@doe.lost",
            "out_currency": "USD",
            "out_amount": out_amount,
            "in_currency": "ETH",
            "in_amount": b"\x00\x98\x96\x80",  # 10000000
            "in_extra_id": "",
            "in_address": "0xd692Cb1346262F584D17B4B470954501f6715a82",
        }

        tx, tx_signature = craft_and_sign_tx(SubCommand.SELL_NG, tx_infos, transaction_id, 100, partner)
        ex.process_transaction(tx)
        ex.check_transaction_signature(tx_signature)

        # format_fiat_amount is called inside check_asset_in_no_display for SELL flows
        ex.check_asset_in_no_display(cal.ETH_CURRENCY_CONFIGURATION.get_conf_for_ticker())

    def test_sell_reject_too_big_exponent(self, backend):
        """Exponent > 255 should be rejected.
        An exponent of 256 is nonsensical for any real fiat currency anyway. We don't try to support it
        """
        out_amount = {"coefficient": b"\x27\x10", "exponent": 256}
        with pytest.raises(ExceptionRAPDU) as e:
            self._perform_sell_up_to_check_asset(backend, out_amount)
        assert e.value.status == Errors.AMOUNT_FORMATTING_FAILED

    def test_sell_reject_too_large_coefficient(self, backend):
        """Coefficient > 8 bytes should be rejected.
        It cannot be represented as a uint64_t, so we refuse to format it rather than silently truncating.
        """
        out_amount = {"coefficient": b"\x01\x00\x00\x00\x00\x00\x00\x00\x01", "exponent": 2}
        with pytest.raises(ExceptionRAPDU) as e:
            self._perform_sell_up_to_check_asset(backend, out_amount)
        assert e.value.status == Errors.AMOUNT_FORMATTING_FAILED


    def test_sell_reject_amount_too_long(self, backend):
        """200 exponent would format an amount too long for the display string, ensure it is rejected.
        """
        out_amount = {"coefficient": b"\x80\x00\x00\x00\x00\x00\x00\x00", "exponent": 200}
        with pytest.raises(ExceptionRAPDU) as e:
            self._perform_sell_up_to_check_asset(backend, out_amount)
        assert e.value.status == Errors.AMOUNT_FORMATTING_FAILED


    def test_sell_accept_large_coefficient(self, backend):
        """Coefficient with the high bit set (>= 2^63) should be accepted.
        It fits in uint64_t and must be formatted as a large positive unsigned value.
        """
        out_amount = {"coefficient": b"\x80\x00\x00\x00\x00\x00\x00\x00", "exponent": 2}
        self._perform_sell_up_to_check_asset(backend, out_amount)
