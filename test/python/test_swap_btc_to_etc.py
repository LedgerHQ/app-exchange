from ledger_bitcoin import Chain
from ledger_bitcoin.client import NewClient

from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.litecoin import LitecoinClient

from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps.exchange_transaction_builder import get_partner_curve, craft_tx, encode_tx, extract_payout_ticker, extract_refund_ticker
from .apps import cal as cal


def test_swap_btc_to_etc(backend, exchange_navigation_helper):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP), name="Default name")

    transaction_id = ex.init_transaction().data
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "payin_address": "bc1q4uj6h8qmdq5699azdagacptw66p202kn0fte56",
        "refund_address": "bc1qer57ma0fzhqys2cmydhuj9cprf9eg0nw922a8j",
        "payout_address": "0x97E22bAc30AAbC10fBEf472B3513812fc717B2fD",
        "payin_extra_id": "",
        "refund_extra_id": "",
        "payout_extra_id": "",
        "currency_from": "BTC",
        "currency_to": "ETC",
        "amount_to_provider": b"\021=\\",
        "amount_to_wallet": b"eA\372:cl@\000",
    }
    fees = 2490

    tx = craft_tx(SubCommand.SWAP, tx_infos, transaction_id)
    ex.process_transaction(tx, fees)
    encoded_tx = encode_tx(SubCommand.SWAP, partner, tx)
    ex.check_transaction_signature(encoded_tx)

    payout_ticker = extract_payout_ticker(SubCommand.SWAP, tx_infos)
    refund_ticker = extract_refund_ticker(SubCommand.SWAP, tx_infos)
    ex.check_payout_address(cal.get_conf_for_ticker(payout_ticker))
    with ex.check_refund_address(cal.get_conf_for_ticker(refund_ticker)):
        exchange_navigation_helper.simple_accept()
    ex.start_signing_transaction()

    # client._client is the Speculos backend within the Ragger client,
    # because BitcoinClient is not Ragger-compatible (yet?)
    with NewClient(backend._client, Chain.MAIN) as btc:
        assert btc.get_master_fingerprint() == bytes.fromhex("f5acc2fd")
