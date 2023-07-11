from ragger.utils import prefix_with_len

from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.litecoin import LitecoinClient

from .signing_authority import SigningAuthority, LEDGER_SIGNER


def test_swap_ltc_to_eth(backend, firmware, exchange_navigation_helper):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

    ex.init_transaction()
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

    ex.process_transaction(tx_infos, fees)
    ex.check_transaction_signature(partner)

    with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER):
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
