import pytest
from typing import Optional, Tuple
from requests.exceptions import ChunkedEncodingError, ConnectionError
from urllib3.exceptions import ProtocolError
from http.client import IncompleteRead

from ragger.backend import RaisePolicy
from ragger.utils import pack_APDU, RAPDU
from ragger.error import ExceptionRAPDU
from ragger.bip import pack_derivation_path
from ragger.navigator import NavInsID

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors
from .apps.tezos import TezosClient, encode_address, XTZ_PACKED_DERIVATION_PATH, StatusCode

from .signing_authority import SigningAuthority, LEDGER_SIGNER

from .utils import ROOT_SCREENSHOT_PATH


def test_tezos_wrong_refund(backend):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "payin_address": b"tz1YPjCVqgimTAPmxZX9egDeTFRCmrTRqmp9",
        "payin_extra_id": b"starlight",
        "refund_address": b"abcdabcd",
        "refund_extra_id": b"",
        "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "payout_extra_id": b"",
        "currency_from": "XTZ",
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


def test_tezos_wrong_payout(backend):
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
        "currency_to": "XTZ",
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


class TezosValidTxPerformer:
    # Default valid tx values used for the tests
    def_path = XTZ_PACKED_DERIVATION_PATH
    def_fees = 100
    def_memo = ""
    def_destination = "e6330795ffe18f873b83cb13662442b87bd98c22"
    def_send_amount = 10000000

    # Helper to use default args if none provided
    def _maybe_default(self, fees, memo, destination, send_amount) -> Tuple[int, str, str, int]:
        fees = self.def_fees if fees is None else fees
        memo = self.def_memo if memo is None else memo
        destination = self.def_destination if destination is None else destination
        send_amount = self.def_send_amount if send_amount is None else send_amount
        return (fees, memo, destination, send_amount)

    # Helper to send a valid TX to the Tezos app, provide parameters to overload te default values
    def perform_tezos_tx(self,
                         backend,
                         fees: Optional[int]=None,
                         memo: Optional[str]=None,
                         destination: Optional[str]=None,
                         send_amount: Optional[int]=None) -> RAPDU:
        fees, memo, destination, send_amount = self._maybe_default(fees, memo, destination, send_amount)

        return TezosClient(backend).send_simple_sign_tx(path=self.def_path,
                                                        fees=fees,
                                                        memo=memo,
                                                        destination=destination,
                                                        send_amount=send_amount)

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
            navigator.navigate_until_text_and_compare(NavInsID.RIGHT_CLICK,
                                                      [NavInsID.BOTH_CLICK],
                                                      "Accept",
                                                      ROOT_SCREENSHOT_PATH,
                                                      test_name)
        ex.start_signing_transaction()


# ##############
# # SWAP tests #
# ##############
class TezosValidSwapPerformer(TezosValidTxPerformer):
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
            "payin_address": encode_address(destination),
            "payin_extra_id": memo.encode(),
            "refund_address": b"tz1YPjCVqgimTAPmxZX9egDeTFRCmrTRqmp9",
            "refund_extra_id": b"",
            "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
            "payout_extra_id": b"",
            "currency_from": "XTZ",
            "currency_to": "ETH",
            "amount_to_provider": int.to_bytes(send_amount, length=8, byteorder='big'),
            "amount_to_wallet": b"\246\333t\233+\330\000",
        }
        self.perform_valid_exchange_tx(backend, navigator, test_name, SubCommand.SWAP, tx_infos, fees)


# Valid swap test with default values
def test_tezos_swap_valid_1(backend, navigator, test_name):
    performer = TezosValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    performer.perform_tezos_tx(backend)


# Valid swap test with non default values
def test_tezos_swap_valid_2(backend, navigator, test_name):
    fees = 10078
    memo = ""
    destination = "e6330795ffe18f873b83cb13662442b87bd98c40"
    send_amount = 446739662

    performer = TezosValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name, fees=fees, memo=memo, destination=destination, send_amount=send_amount)
    performer.perform_tezos_tx(backend, fees=fees, memo=memo, destination=destination, send_amount=send_amount)


# Make a valid swap and then ask a second signature
def test_tezos_swap_refuse_double_sign(backend, navigator, test_name):
    performer = TezosValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    performer.perform_tezos_tx(backend)

    with pytest.raises((ChunkedEncodingError, ConnectionError, ProtocolError, IncompleteRead)):
        performer.perform_tezos_tx(backend)


# Test swap with a malicious Tezos TX with tampered fees
def test_tezos_swap_wrong_fees(backend, navigator, test_name):
    performer = TezosValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_tezos_tx(backend, fees=performer.def_fees + 100)
    assert rapdu.status == StatusCode.EXC_REJECT


# # Test swap with a malicious Tezos TX with tampered memo
# def test_tezos_swap_wrong_memo(backend, navigator, test_name):
#     performer = TezosValidSwapPerformer()
#     performer.perform_valid_swap(backend, navigator, test_name)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_tezos_tx(backend, memo=performer.def_memo + "0")
#     assert rapdu.status == StatusCode.EXC_REJECT


# Test swap with a malicious Tezos TX with tampered dest
def test_tezos_swap_wrong_dest(backend, navigator, test_name):
    performer = TezosValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_tezos_tx(backend, destination="e6330795ffe18f873b83cb13662442b87bd98c45")
    assert rapdu.status == StatusCode.EXC_REJECT


# Test swap with a malicious Tezos TX with tampered amount
def test_tezos_swap_wrong_amount(backend, navigator, test_name):
    performer = TezosValidSwapPerformer()
    performer.perform_valid_swap(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_tezos_tx(backend, send_amount=performer.def_send_amount + 351)
    assert rapdu.status == StatusCode.EXC_REJECT


# ##############
# # FUND tests #
# ##############

class TezosValidFundPerformer(TezosValidTxPerformer):
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
            "in_currency": "XTZ",
            "in_amount": int.to_bytes(send_amount, length=4, byteorder='big'),
            "in_address": encode_address(destination),
        }
        self.perform_valid_exchange_tx(backend, navigator, test_name, SubCommand.FUND, tx_infos, fees)


# Valid fund test with default values
def test_tezos_fund_valid_1(backend, navigator, test_name):
    performer = TezosValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    performer.perform_tezos_tx(backend)


# Valid fund test with non default values
def test_tezos_fund_valid_2(backend, navigator, test_name):
    fees = 10078
    destination="e6330795ffe18f873b83cb13662442b87bd98c40"
    send_amount = 446739662

    performer = TezosValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name, fees=fees, destination=destination, send_amount=send_amount)
    performer.perform_tezos_tx(backend, fees=fees, destination=destination, send_amount=send_amount)


# Make a valid fund and then ask a second signature
def test_tezos_fund_refuse_double_sign(backend, navigator, test_name):
    performer = TezosValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    performer.perform_tezos_tx(backend)

    with pytest.raises((ChunkedEncodingError, ConnectionError, ProtocolError, IncompleteRead)):
        performer.perform_tezos_tx(backend)


# Test fund with a malicious Tezos TX with tampered fees
def test_tezos_fund_wrong_fees(backend, navigator, test_name):
    performer = TezosValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_tezos_tx(backend, fees=performer.def_fees + 100)
    assert rapdu.status == StatusCode.EXC_REJECT


# # Test fund with a malicious Tezos TX with tampered memo
# def test_tezos_fund_wrong_memo(backend, navigator, test_name):
#     performer = TezosValidFundPerformer()
#     performer.perform_valid_fund(backend, navigator, test_name)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_tezos_tx(backend, memo=performer.def_memo + "0")
#     assert rapdu.status == StatusCode.EXC_REJECT


# Test fund with a malicious Tezos TX with tampered dest
def test_tezos_fund_wrong_dest(backend, navigator, test_name):
    performer = TezosValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_tezos_tx(backend, destination="e6330795ffe18f873b83cb13662442b87bd98c45")
    assert rapdu.status == StatusCode.EXC_REJECT


# Test fund with a malicious Tezos TX with tampered amount
def test_tezos_fund_wrong_amount(backend, navigator, test_name):
    performer = TezosValidFundPerformer()
    performer.perform_valid_fund(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_tezos_tx(backend, send_amount=performer.def_send_amount + 351)
    assert rapdu.status == StatusCode.EXC_REJECT


# ##############
# # SELL tests #
# ##############

class TezosValidSellPerformer(TezosValidTxPerformer):
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
            "in_currency": "XTZ",
            "in_amount": int.to_bytes(send_amount, length=4, byteorder='big'),
            "in_address": encode_address(destination),
        }
        self.perform_valid_exchange_tx(backend, navigator, test_name, SubCommand.SELL, tx_infos, fees)


# Valid sell test with default values
def test_tezos_sell_valid_1(backend, navigator, test_name):
    performer = TezosValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    performer.perform_tezos_tx(backend)


# Valid sell test with non default values
def test_tezos_sell_valid_2(backend, navigator, test_name):
    fees = 10078
    destination="e6330795ffe18f873b83cb13662442b87bd98c40"
    send_amount = 446739662

    performer = TezosValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name, fees=fees, destination=destination, send_amount=send_amount)
    performer.perform_tezos_tx(backend, fees=fees, destination=destination, send_amount=send_amount)


# Make a valid sell and then ask a second signature
def test_tezos_sell_refuse_double_sign(backend, navigator, test_name):
    performer = TezosValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    performer.perform_tezos_tx(backend)

    with pytest.raises((ChunkedEncodingError, ConnectionError, ProtocolError, IncompleteRead)):
        performer.perform_tezos_tx(backend)


# Test sell with a malicious Tezos TX with tampered fees
def test_tezos_sell_wrong_fees(backend, navigator, test_name):
    performer = TezosValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_tezos_tx(backend, fees=performer.def_fees + 100)
    assert rapdu.status == StatusCode.EXC_REJECT


# # Test sell with a malicious Tezos TX with tampered memo
# def test_tezos_sell_wrong_memo(backend, navigator, test_name):
#     performer = TezosValidSellPerformer()
#     performer.perform_valid_sell(backend, navigator, test_name)
#     backend.raise_policy = RaisePolicy.RAISE_NOTHING
#     rapdu = performer.perform_tezos_tx(backend, memo=performer.def_memo + "0")
#     assert rapdu.status == StatusCode.EXC_REJECT


# Test sell with a malicious Tezos TX with tampered dest
def test_tezos_sell_wrong_dest(backend, navigator, test_name):
    performer = TezosValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_tezos_tx(backend, destination="e6330795ffe18f873b83cb13662442b87bd98c45")
    assert rapdu.status == StatusCode.EXC_REJECT


# Test sell with a malicious Tezos TX with tampered amount
def test_tezos_sell_wrong_amount(backend, navigator, test_name):
    performer = TezosValidSellPerformer()
    performer.perform_valid_sell(backend, navigator, test_name)
    backend.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu = performer.perform_tezos_tx(backend, send_amount=performer.def_send_amount + 351)
    assert rapdu.status == StatusCode.EXC_REJECT
