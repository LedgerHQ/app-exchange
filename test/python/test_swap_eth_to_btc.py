from time import sleep

import pytest
from ragger.backend.interface import RaisePolicy
from ragger.utils import pack_APDU, RAPDU
from ragger.error import ExceptionRAPDU

from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.ethereum import EthereumClient, ERR_SILENT_MODE_CHECK_FAILED
from .utils import concatenate


def prepare_exchange(client, firmware, amount: str):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    ex.init_transaction()
    ex.set_partner_key()
    ex.check_partner_key()

    tx_infos = {
        "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
        "payin_extra_id": b"",
        "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "refund_extra_id": b"",
        "payout_address": b"bc1qwpgezdcy7g6khsald7cww42lva5g5dmasn6y2z",
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
    with pytest.raises(RAPDU):
        eth.sign(extra_payload=bytes.fromhex("ec09850684ee180082520894d692cb1346262f584d17b4b470954501f6715a8288" + wrong_amount + "80018080"))


def test_swap_eth_to_btc_ok(client, firmware):
    amount = '013fc3a717fb5000'
    prepare_exchange(client, firmware, amount)
    eth = EthereumClient(client, derivation_path=bytes.fromhex("058000002c8000003c800000000000000000000000"))
    eth.get_public_key()
    eth.sign(extra_payload=bytes.fromhex("ec09850684ee180082520894d692cb1346262f584d17b4b470954501f6715a8288" + amount + "80018080"))


def test_swap_eth_to_btc_evil(client, firmware):
    amount = '0f95b28cd2c38000'
    prepare_exchange(client, firmware, amount)

    eth = EthereumClient(client, derivation_path=bytes.fromhex("058000002c8000003c800000000000000000000000"))
    eth.set_plugin()
    eth.provide_nft_information()
    eth.sign()
    client.set_raise_policy(RaisePolicy.RAISE_ALL)
    try:
        eth.sign_more()
    except ExceptionRAPDU as rapdu:
        assert rapdu.status == ERR_SILENT_MODE_CHECK_FAILED.status, f"Received APDU status {hex(rapdu.status)}, expected {hex(ERR_SILENT_MODE_CHECK_FAILED.status)}"

# RAISE_NOTHING
# raise_policy

#     eth = EthereumClient(client, derivation_path=bytes.fromhex("058000002c8000003c800000000000000000000000"))
#     eth.get_public_key()
#     eth.sign(extra_payload=bytes.fromhex("ec09850684ee180082520894d692cb1346262f584d17b4b470954501f6715a8288" + amount + "80018080"))
#     apdus = ['e01600007301010645524337323160f80121c31a0d46b5279700f9df786054aa5ee542842e0e0000000000000001000147304502202e2282d7d3ea714da283010f517af469e1d59654aaee0fc438f017aa557eaea50221008b369679381065bbe01135723a4f9adb229295017d37c4d30138b90a51cf6ab6',
# 'e01400007001010752617269626c6560f80121c31a0d46b5279700f9df786054aa5ee500000000000000010001473045022025696986ef5f0ee2f72d9c6e41d7e2bf2e4f06373ab26d73ebe326c7fd4c7a6602210084f6b064d8750ae68ed5dd012296f37030390ec06ff534c5da6f0f4a4460af33',
# 'e004000096058000002c8000003c800000000000000000000000f88a0a852c3ce1ec008301f5679460f80121c31a0d46b5279700f9df786054aa5ee580b86442842e0e0000000000000000000000006cbcd73cd8e8a42844662f0a0e76d7f79afd933d000000000000000000000000c2907efcce4011c491bbeda8a0fa63ba7aab596c000000000000000000000000000000000000000000000000',
# 'e00480000b0000000000112999018080']

#     for apdu in apdus:
#         data = client.raw_exchange(bytes.fromhex(apdu))
#         print(data)

