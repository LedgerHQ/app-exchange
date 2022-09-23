from .apps.exchange import ExchangeClient, Rate, SubCommand
from ragger.utils import RAPDU
from ragger.backend import RaisePolicy
import pytest

SIGN_VERIFICATION_FAIL = 0x9D1A

SWAP_TX_INFOS = {
     "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
     "payin_extra_id": b"",
     "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
     "refund_extra_id": b"",
     "payout_address": b"bc1qer57ma0fzhqys2cmydhuj9cprf9eg0nw922a8j",
     "payout_extra_id": b"",
     "currency_from": "ETH",
     "currency_to": "BTC",
     "amount_to_provider": bytes.fromhex("013fc3a717fb5000"),
     "amount_to_wallet": b"\x0b\xeb\xc2\x00",
}

FUND_TX_INFOS = {
    "user_id": "John Wick",
    "account_name": "Remember Daisy",
    "in_currency": "ETH",
    "in_amount": b"\032\200\250]$T\000",
    "in_address": "0x252fb4acbe0de4f0bd2409a5ed59a71e4ef1d2bc"
}

SELL_TX_INFOS = {
    "trader_email": "john@doe.lost",
    "out_currency": "USD",
    "out_amount": {"coefficient": b"\x01", "exponent": 3},
    "in_currency": "ETH",
    "in_amount": b"\032\200\250]$T\000",
    "in_address": "0x252fb4acbe0de4f0bd2409a5ed59a71e4ef1d2bc"
}

TX_INFOS = {
    "SWAP": SWAP_TX_INFOS,
    "FUND": FUND_TX_INFOS,
    "SELL": SELL_TX_INFOS,
}
SUB_COMMAND = {
    "SWAP": SubCommand.SWAP,
    "FUND": SubCommand.FUND,
    "SELL": SubCommand.SELL,
}

FEES = bytes.fromhex("0216c86b20c000") # ETH 0.000588


# CHECK THAT A PARTNER SIGNED BY THE LEDGER KEY BUT DIFFERENT THAN THE SET IS REFUSED

@pytest.mark.parametrize("operation", ["SWAP", "FUND", "SELL"])
def test_fake_partner_credentials_sent(client, firmware, operation):
    ex = ExchangeClient(client, Rate.FIXED, SUB_COMMAND[operation])
    ex.init_transaction()
    ex.set_partner_key(use_main_partner = False)

    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.check_partner_key(use_test_key=False)
    assert rapdu.status == SIGN_VERIFICATION_FAIL


# CHECK THAT A PARTNER NOT SIGNED BY THE LEDGER KEY IS REFUSED

@pytest.mark.parametrize("operation", ["SWAP", "FUND", "SELL"])
def test_fake_partner_credentials_signed(client, firmware, operation):
    ex = ExchangeClient(client, Rate.FIXED, SUB_COMMAND[operation])
    ex.init_transaction()
    ex.set_partner_key()

    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.check_partner_key(use_test_key=False)
    assert rapdu.status == SIGN_VERIFICATION_FAIL


# CHECK THAT A TRANSACTION INFORMATION NOT SIGNED BY THE PARTNER KEY IS REFUSED

@pytest.mark.parametrize("operation", ["SWAP", "FUND", "SELL"])
def test_fake_transaction_infos(client, firmware, operation):
    ex = ExchangeClient(client, Rate.FIXED, SUB_COMMAND[operation])
    ex.init_transaction()
    ex.set_partner_key()
    ex.check_partner_key()
    ex.process_transaction(TX_INFOS[operation], FEES)

    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.check_transaction(use_main_partner = False)
    assert rapdu.status == SIGN_VERIFICATION_FAIL


# CHECK THAT A COIN CONFIGURATION NOT SIGNED BY THE LEDGER KEY IS REFUSED

@pytest.mark.parametrize("operation", ["SWAP", "FUND", "SELL"])
def test_fake_payout_coin_configuration(client, firmware, operation):
    ex = ExchangeClient(client, Rate.FIXED, SUB_COMMAND[operation])
    ex.init_transaction()
    ex.set_partner_key()
    ex.check_partner_key()
    ex.process_transaction(TX_INFOS[operation], FEES)
    ex.check_transaction()

    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.check_address(right_clicks=0, use_test_key_for_payout=False)
    assert rapdu.status == SIGN_VERIFICATION_FAIL

@pytest.mark.parametrize("operation", ["SWAP"]) # Swap only
def test_fake_refund_coin_configuration(client, firmware, operation):
    ex = ExchangeClient(client, Rate.FIXED, SUB_COMMAND[operation])
    ex.init_transaction()
    ex.set_partner_key()
    ex.check_partner_key()
    ex.process_transaction(TX_INFOS[operation], FEES)
    ex.check_transaction()

    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.check_address(right_clicks=0, use_test_key_for_refund=False)
    assert rapdu.status == SIGN_VERIFICATION_FAIL
