from ledger_bitcoin import Chain
from ledger_bitcoin.client import NewClient

from ragger.navigator import NavInsID

from .apps.exchange import ExchangeClient, Rate, SubCommand
from .apps.litecoin import LitecoinClient

from .signing_authority import SigningAuthority, LEDGER_SIGNER

from .utils import ROOT_SCREENSHOT_PATH


def test_swap_btc_to_etc(backend, firmware, navigator, test_name):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
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
        "currency_from": "BTC",
        "currency_to": "ETC",
        "amount_to_provider": b"\021=\\",
        "amount_to_wallet": b"eA\372:cl@\000",
    }
    fees = b'\t\xba'

    ex.process_transaction(tx_infos, fees)
    ex.check_transaction_signature(partner)

    with ex.check_address(payout_signer=LEDGER_SIGNER, refund_signer=LEDGER_SIGNER):
        navigator.navigate_until_text_and_compare(NavInsID.RIGHT_CLICK,
                                                  [NavInsID.BOTH_CLICK],
                                                  "Accept",
                                                  ROOT_SCREENSHOT_PATH,
                                                  test_name)
    ex.start_signing_transaction()

    # client._client is the Speculos backend within the Ragger client,
    # because BitcoinClient is not Ragger-compatible (yet?)
    with NewClient(backend._client, Chain.MAIN) as btc:
        assert btc.get_master_fingerprint() == bytes.fromhex("f5acc2fd")
