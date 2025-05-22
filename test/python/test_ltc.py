import pytest
from ragger.utils import prefix_with_len

from ledger_app_clients.exchange.client import ExchangeClient, Rate, SubCommand
from .apps.litecoin import LitecoinClient

from ledger_app_clients.exchange.signing_authority import SigningAuthority, LEDGER_SIGNER
from ledger_app_clients.exchange.transaction_builder import get_partner_curve, craft_and_sign_tx, ALL_SUBCOMMANDS, get_credentials
from .apps import cal as cal

CURRENCY_FROM = cal.LTC_CURRENCY_CONFIGURATION
CURRENCY_TO = cal.ETH_CURRENCY_CONFIGURATION

SWAP_TX_INFOS = {
    "payin_address": "LKY4hyq7ucxtdGoQ6ajkwv4ddTNA4WpYhF",
    "refund_address": "MJovkMvQ2rXXUj7TGVvnQyVMWghSdqZsmu",
    "payout_address": "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
    "payin_extra_id": "",
    "refund_extra_id": "",
    "payout_extra_id": "",
    "currency_from": CURRENCY_FROM.ticker,
    "currency_to": CURRENCY_TO.ticker,
    "amount_to_provider": b"\010T2V",
    "amount_to_wallet": b"\246\333t\233+\330\000",
}
FUND_TX_INFOS = {
    "user_id": "John Wick",
    "account_name": "Remember Daisy",
    "in_currency": CURRENCY_FROM.ticker,
    "in_amount": b"\010T2V",
    "in_address": "LKY4hyq7ucxtdGoQ6ajkwv4ddTNA4WpYhF"
}
SELL_TX_INFOS = {
    "trader_email": "john@doe.lost",
    "out_currency": "USD",
    "out_amount": {"coefficient": b"\x01", "exponent": 3},
    "in_currency": CURRENCY_FROM.ticker,
    "in_amount": b"\010T2V",
    "in_address": "LKY4hyq7ucxtdGoQ6ajkwv4ddTNA4WpYhF"
}
TX_INFOS = {
    SubCommand.SWAP: SWAP_TX_INFOS,
    SubCommand.SWAP_NG: SWAP_TX_INFOS,
    SubCommand.FUND: FUND_TX_INFOS,
    SubCommand.FUND_NG: FUND_TX_INFOS,
    SubCommand.SELL: SELL_TX_INFOS,
    SubCommand.SELL_NG: SELL_TX_INFOS,
}

######################################################################################################
# /!\ This test is also used to check the legacy subcommands SWAP, SELL, and FUND. Don't upgrade /!\ #
# /!\ This test is also used to check the check_address_and_display commands.      Don't upgrade /!\ #
######################################################################################################

@pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
def test_ltc(backend, exchange_navigation_helper, subcommand):
    suffix = "_" + str(subcommand).split('.')[1].split('_')[0].lower()
    exchange_navigation_helper.set_test_name_suffix(suffix)

    ex = ExchangeClient(backend, Rate.FIXED, subcommand)
    partner = SigningAuthority(curve=get_partner_curve(subcommand), name="Default name")

    transaction_id = ex.init_transaction().data
    credentials = get_credentials(subcommand, partner)
    ex.set_partner_key(credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(credentials))

    fees = 339

    tx, tx_signature = craft_and_sign_tx(subcommand, TX_INFOS[subcommand], transaction_id, fees, partner)
    ex.process_transaction(tx)
    ex.check_transaction_signature(tx_signature)

    from_configuration = CURRENCY_FROM.get_conf_for_ticker()
    if subcommand == SubCommand.SWAP or subcommand == SubCommand.SWAP_NG:
        to_configuration = CURRENCY_TO.get_conf_for_ticker()
        ex.check_payout_address(to_configuration)

        # Request the final address check and UI approval request on the device
        with ex.check_refund_address(from_configuration):
            exchange_navigation_helper.simple_accept()
    else:
        with ex.check_asset_in(from_configuration):
            exchange_navigation_helper.simple_accept()
    ex.start_signing_transaction()

    ltc = LitecoinClient(backend)

    ltc.get_public_key(bytes.fromhex('058000005480000002800000000000000000000001'))
    ltc.get_coin_version()
    ltc.get_trusted_input(bytes.fromhex('000000000200000001'))
    ltc.get_trusted_input(bytes.fromhex('5afe770dd416a3e3a7852ffc7c2cb03ec2e4f1709f07d2a61776f27461e455290000000000'))
    ltc.get_trusted_input(bytes.fromhex('ffffffff'))
    ltc.get_trusted_input(bytes.fromhex('01'))
    ltc.get_trusted_input(bytes.fromhex('a9335408000000001600146efd74d16ca7e5da5ce06d449fb9124fd6af05cd'))
    result = ltc.get_trusted_input(bytes.fromhex('00000000')).data
    ltc.get_public_key(bytes.fromhex('058000005480000002800000000000000000000000'))
    ltc.hash_input(bytes.fromhex('0100000001'))
    ltc.hash_input(bytes.fromhex('01') + prefix_with_len(result) + bytes.fromhex('00'))
    ltc.hash_input(bytes.fromhex('00000000'))
    ltc.hash_input(bytes.fromhex('0156325408000000001976a914036cdde130e7b93b86d27425145082bc2b6c724488ac'), finalize=True)
