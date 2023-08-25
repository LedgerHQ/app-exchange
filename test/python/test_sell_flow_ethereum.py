from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.ethereum import EthereumClient, eth_amount_to_wei

from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps.exchange_transaction_builder import get_partner_curve, craft_tx, encode_tx, extract_payout_ticker, extract_refund_ticker
from .apps import cal as cal


def test_sell_flow(backend, exchange_navigation_helper):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SELL)
    partner = SigningAuthority(curve=get_partner_curve(SubCommand.SELL), name="Default name")

    transaction_id = ex.init_transaction().data
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

    tx = craft_tx(SubCommand.SELL, tx_infos, transaction_id)
    ex.process_transaction(tx, eth_amount_to_wei(0.004520765))
    encoded_tx = encode_tx(SubCommand.SELL, partner, tx)
    ex.check_transaction_signature(encoded_tx)
    with ex.check_asset_in(cal.get_conf_for_ticker(tx_infos["in_currency"])):
        exchange_navigation_helper.simple_accept()
    ex.start_signing_transaction()

    eth = EthereumClient(backend)
    assert eth.get_public_key().status == 0x9000
    # The original bug was that the Ethereum app was returning just after
    # launch, and the first Ethereum:get_public_key call was in fact catched
    # by the Exchange app and interpreted as an Exchange::get_version call.
    # Exchange version are on 3 bytes, so we check the call does not return
    # 3 bytes of data
    assert len(eth.get_public_key().data) > 3
    assert eth.sign().status == 0x9000
