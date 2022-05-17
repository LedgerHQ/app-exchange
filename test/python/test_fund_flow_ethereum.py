from time import sleep

from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.ethereum import EthereumClient


def test_fund_flow(client):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.FUND)
    eth = EthereumClient(client)
    ex.init_transaction()
    ex.set_partner_key()
    ex.check_partner_key()

    tx_infos = {
        'user_id': "John Wick",
        'account_name': "Remember Daisy",
        'in_currency': "ETH",
        'in_amount': b"\032\200\250]$T\000",
        'in_address': "0x252fb4acbe0de4f0bd2409a5ed59a71e4ef1d2bc"
    }

    ex.process_transaction(tx_infos, b'\x10\x0f\x9c\x9f\xf0"\x00')
    ex.check_transaction()
    ex.check_address(right_clicks=5)
    ex.start_signing_transaction()

    sleep(0.1)

    assert eth.get_public_key().status == 0x9000
    assert eth.sign().status == 0x9000
