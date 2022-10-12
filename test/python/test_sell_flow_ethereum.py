from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.ethereum import EthereumClient

from .signing_authority import SigningAuthority, LEDGER_SIGNER


def test_sell_flow(client, firmware):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SELL)
    eth = EthereumClient(client)
    partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "trader_email": "john@doe.lost",
        "out_currency": "USD",
        "out_amount": {"coefficient": b"\x01", "exponent": 3},
        "in_currency": "ETH",
        "in_amount": b"\032\200\250]$T\000",
        "in_address": "0x252fb4acbe0de4f0bd2409a5ed59a71e4ef1d2bc"
    }

    ex.process_transaction(tx_infos, b'\x10\x0f\x9c\x9f\xf0"\x00')
    ex.check_transaction_signature(partner)

    right_clicks = {
        "nanos": 5,
        "nanox": 5,
        "nanosp": 5
    }
    ex.check_address(LEDGER_SIGNER, right_clicks=right_clicks[firmware.device])
    ex.start_signing_transaction()

    assert eth.get_public_key().status == 0x9000
    # The original bug was that the Ethereum app was returning just after
    # launch, and the first Ethereum:get_public_key call was in fact catched
    # by the Exchange app and interpreted as an Exchange::get_version call.
    # Exchange version are on 3 bytes, so we check the call does not return
    # 3 bytes of data
    assert len(eth.get_public_key().data) > 3
    assert eth.sign().status == 0x9000
