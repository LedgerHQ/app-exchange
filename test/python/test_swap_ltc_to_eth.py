from ragger.utils import prefix_with_len

from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.litecoin import LitecoinClient

from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps.exchange_transaction_builder import get_partner_curve, craft_tx, encode_tx, extract_payout_ticker, extract_refund_ticker
from .apps import cal as cal


def test_swap_ltc_to_eth(backend, exchange_navigation_helper):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP), name="Default name")

    transaction_id = ex.init_transaction().data
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "payin_address": "LKY4hyq7ucxtdGoQ6ajkwv4ddTNA4WpYhF",
        "refund_address": "MJovkMvQ2rXXUj7TGVvnQyVMWghSdqZsmu",
        "payout_address": "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "payin_extra_id": "",
        "refund_extra_id": "",
        "payout_extra_id": "",
        "currency_from": "LTC",
        "currency_to": "ETH",
        "amount_to_provider": b"\010T2V",
        "amount_to_wallet": b"\246\333t\233+\330\000",
    }
    fees = 339

    tx = craft_tx(SubCommand.SWAP, tx_infos, transaction_id)
    ex.process_transaction(tx, fees)
    encoded_tx = encode_tx(SubCommand.SWAP, partner, tx)
    ex.check_transaction_signature(encoded_tx)

    payout_ticker = extract_payout_ticker(SubCommand.SWAP, tx_infos)
    refund_ticker = extract_refund_ticker(SubCommand.SWAP, tx_infos)
    with ex.check_address(cal.get_conf_for_ticker(payout_ticker), cal.get_conf_for_ticker(refund_ticker)):
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
