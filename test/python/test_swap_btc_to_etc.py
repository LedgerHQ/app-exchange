from time import sleep

from ledger_bitcoin import Chain
from ledger_bitcoin.client import NewClient

from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.litecoin import LitecoinClient

from .signing_authority import SigningAuthority, LEDGER_SIGNER


def test_swap_btc_to_etc(client, firmware):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

    ex.init_transaction()
    ex.set_partner_key(partner.credentials)
    ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))

    tx_infos = {
        "payin_address": "bc1q4uj6h8qmdq5699azdagacptw66p202kn0fte56",
        "refund_address": "bc1qer57ma0fzhqys2cmydhuj9cprf9eg0nw922a8j",
        "payout_address": "0x97E22bAc30AAbC10fBEf472B3513812fc717B2fD",
        "payin_extra_id": "",
        "refund_extra_id": "",
        "payout_extra_id": "",
        "currency_from": "btc",
        "currency_to": "etc",
        "amount_to_provider": b"\021=\\",
        "amount_to_wallet": b"eA\372:cl@\000",
    }
    fees = b'\t\xba'

    ex.process_transaction(tx_infos, fees)
    ex.check_transaction_signature(partner)

    right_clicks = {
        "nanos": 4,
        "nanox": 4,
        "nanosp": 4
    }

    ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER, right_clicks=right_clicks[firmware.device])
    ex.start_signing_transaction()

    sleep(0.1)

    # client._client is the Speculos backend within the Ragger client,
    # because BitcoinClient is not Ragger-compatible (yet?)
    with NewClient(client._client, Chain.MAIN) as btc:
        assert btc.get_master_fingerprint() == bytes.fromhex("f5acc2fd")
