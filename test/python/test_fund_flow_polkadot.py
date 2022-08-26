from time import sleep

from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.polkadot import DOT_PACKED_DERIVATION_PATH, DOT_CONF, DOT_CONF_DER_SIGNATURE
from .utils import concatenate

def test_fund_flow_dot(client, exchange):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.FUND)
    #eth = PolkadotClient(client)
    ex.init_transaction()
    ex.set_partner_key()
    ex.check_partner_key()

    tx_infos = {
        "user_id": "John Wick",
        "account_name": "Remember Daisy",
        "in_currency": "DOT",
        "in_amount": b"\032\200\250]$T\000",
        #"in_address": "0x31345477537158456f43504b3751374a6e6b3252467a62505a58707073787a3234624861513766616b77696f3744466e"
        "in_address": "14TwSqXEoCPK7Q7Jnk2RFzbPZXppsxz24bHaQ7fakwio7DFn"
    }

    ex.process_transaction(tx_infos, b'\x10\x0f\x9c\x9f\xf0"\x00')
    ex.check_transaction()

    right_clicks = {
        "nanos": 5,
        "nanox": 5,
        "nanosp": 5
    }
    payload = (concatenate(DOT_CONF)
                   + DOT_CONF_DER_SIGNATURE
                   + concatenate(DOT_PACKED_DERIVATION_PATH))
    ex.check_address(right_clicks=right_clicks[exchange.firmware.device],coin1_payload=payload)
    #ex.start_signing_transaction()

    sleep(0.1)
