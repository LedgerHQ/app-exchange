from time import sleep

import pytest
from ragger.error import ApplicationError

from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.ethereum import EthereumClient
from .utils import concatenate


def prepare_exchange(client, firmware, amount: str):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    ex.init_transaction()
    ex.set_partner_key()
    ex.check_partner_key()

    tx_infos = {
        "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
        "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "payout_address": b"bc1qer57ma0fzhqys2cmydhuj9cprf9eg0nw922a8j",
        "payin_extra_id": "",
        "refund_extra_id": "",
        "payout_extra_id": b"",
        "currency_from": "ETH",
        "currency_to": "BTC",
        "amount_to_provider": bytes.fromhex(amount), # ETH 1.123
        "amount_to_wallet": b"\x0b\xeb\xc2\x00",
    }
    fees = b'\x01'

    ex.process_transaction(tx_infos, fees)
    ex.check_transaction()

    right_clicks = {
        "nanos": 6,
        "nanox": 4,
        "nanosp": 4
    }

    ex.check_address(right_clicks=right_clicks[firmware.device])
    ex.start_signing_transaction()
    sleep(0.1)

def test_swap_eth_to_btc_wrong_amount(client, firmware):
    amount       = '013fc3a717fb5000'
    wrong_amount = '013fc3a6be932100'
    prepare_exchange(client, firmware, amount)
    eth = EthereumClient(client, derivation_path=bytes.fromhex("058000002c8000003c800000000000000000000000"))
    eth.get_public_key()
    with pytest.raises(ApplicationError):
        eth.sign(extra_payload=bytes.fromhex("ec09850684ee180082520894d692cb1346262f584d17b4b470954501f6715a8288" + wrong_amount + "80018080"))


def test_swap_eth_to_btc_ok(client, firmware):
    amount = '013fc3a717fb5000'
    prepare_exchange(client, firmware, amount)
    eth = EthereumClient(client, derivation_path=bytes.fromhex("058000002c8000003c800000000000000000000000"))
    eth.get_public_key()
    eth.sign(extra_payload=bytes.fromhex("ec09850684ee180082520894d692cb1346262f584d17b4b470954501f6715a8288" + amount + "80018080"))
