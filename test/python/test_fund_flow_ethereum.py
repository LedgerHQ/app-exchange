from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.ethereum import EthereumClient, eth_amount_to_wei

from .signing_authority import SigningAuthority, LEDGER_SIGNER


def test_fund_flow_ethereum_max_partner_name_length(backend, exchange_navigation_helper):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.FUND)
    partner = SigningAuthority(curve=ex.partner_curve, name="PARTNER_NAME_12")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "user_id": "John Wick",
        "account_name": "Remember Daisy",
        "in_currency": "ETH",
        "in_amount": b"\032\200\250]$T\000",
        "in_address": "0x252fb4acbe0de4f0bd2409a5ed59a71e4ef1d2bc"
    }

    ex.process_transaction(tx_infos, eth_amount_to_wei(0.004520765))
    ex.check_transaction_signature(partner)
    with ex.check_address(LEDGER_SIGNER):
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


def test_fund_flow_ethereum_min_partner_name_length(backend, exchange_navigation_helper):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.FUND)
    partner = SigningAuthority(curve=ex.partner_curve, name="PAR")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "user_id": "John Wick",
        "account_name": "Remember Daisy",
        "in_currency": "ETH",
        "in_amount": b"\032\200\250]$T\000",
        "in_address": "0x252fb4acbe0de4f0bd2409a5ed59a71e4ef1d2bc"
    }

    ex.process_transaction(tx_infos, eth_amount_to_wei(0.004520765))
    ex.check_transaction_signature(partner)
    with ex.check_address(LEDGER_SIGNER):
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
