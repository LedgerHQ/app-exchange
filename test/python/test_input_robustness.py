from ragger.utils import RAPDU, prefix_with_len
from ragger.backend import RaisePolicy

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors, TICKER_TO_CONF, TICKER_TO_PACKED_DERIVATION_PATH, Command
from .signing_authority import SigningAuthority, LEDGER_SIGNER

class TestRobustnessSET_PARTNER_KEY:

    def test_robustness_set_partner_key_name_too_long(self, backend):
        name = "PARTNER_NAME_123" # Too long
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name=name)

        ex.init_transaction()
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.set_partner_key(partner.credentials)
        assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

    def test_robustness_set_partner_key_name_too_short(self, backend):
        name = "PA" # Too short
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name=name)

        ex.init_transaction()
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.set_partner_key(partner.credentials)
        assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

    def test_robustness_set_partner_key_name_none(self, backend):
        name = "" # Nothing
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name=name)

        ex.init_transaction()
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.set_partner_key(partner.credentials)
        assert rapdu.status == Errors.INCORRECT_COMMAND_DATA


class TestRobustnessCHECK_ADDRESS:
    tx_infos = {
        "payin_address": b"GCKUD4BHIYSAYHU7HBB5FDSW6CSYH3GSOUBPWD2KE7KNBERP4BSKEJDV",
        "payin_extra_id": b"",
        "refund_address": b"abcdabcd",
        "refund_extra_id": b"",
        "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "payout_extra_id": b"",
        "currency_from": "XLM",
        "currency_to": "ETH",
        "amount_to_provider": int.to_bytes(1000, length=8, byteorder='big'),
        "amount_to_wallet": b"\246\333t\233+\330\000",
    }
    fees_bytes = int.to_bytes(100, length=4, byteorder='big')

    payout_currency_conf = TICKER_TO_CONF[tx_infos["currency_to"].upper()]
    signed_payout_conf = LEDGER_SIGNER.sign(payout_currency_conf)
    payout_currency_derivation_path = TICKER_TO_PACKED_DERIVATION_PATH[tx_infos["currency_to"].upper()]

    refund_currency_conf = TICKER_TO_CONF[tx_infos["currency_from"].upper()]
    signed_refund_conf = LEDGER_SIGNER.sign(refund_currency_conf)
    refund_currency_derivation_path = TICKER_TO_PACKED_DERIVATION_PATH[tx_infos["currency_from"].upper()]

    def _restart_test(self, backend, ex, partner):
        ex.init_transaction()
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        ex.process_transaction(self.tx_infos, self.fees_bytes)
        ex.check_transaction_signature(partner)

    def test_robustness_check_check_payout_address(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

        payloads_to_test = (
            # Nothing
            b'',
            # Empty payout_currency_conf
            prefix_with_len(b'') + self.signed_payout_conf + prefix_with_len(self.payout_currency_derivation_path),
            # No signed_payout_conf
            prefix_with_len(self.payout_currency_conf) + b'' + prefix_with_len(self.payout_currency_derivation_path),
            # Empty payout_currency_derivation_path
            prefix_with_len(self.payout_currency_conf) + self.signed_payout_conf + prefix_with_len(b''),
            # Trailing bytes
            prefix_with_len(self.payout_currency_conf) + self.signed_payout_conf + prefix_with_len(self.payout_currency_derivation_path) + b"a",
        )

        for payout_payload in payloads_to_test:
            backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
            self._restart_test(backend, ex, partner)
            backend.raise_policy = RaisePolicy.RAISE_NOTHING
            rapdu = ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_payload)
            assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

    def test_robustness_check_check_refund_address(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name="Default name")
        backend.raise_policy = RaisePolicy.RAISE_NOTHING

        payloads_to_test = (
            # Nothing
            b'',
            # Empty refund_currency_conf
            prefix_with_len(b'') + self.signed_refund_conf + prefix_with_len(self.refund_currency_derivation_path),
            # No signed_refund_conf
            prefix_with_len(self.refund_currency_conf) + b'' + prefix_with_len(self.refund_currency_derivation_path),
            # Empty refund_currency_derivation_path
            prefix_with_len(self.refund_currency_conf) + self.signed_refund_conf + prefix_with_len(b''),
            # Trailing bytes
            prefix_with_len(self.refund_currency_conf) + self.signed_refund_conf + prefix_with_len(self.refund_currency_derivation_path) + b"a",
        )
        payout_payload = prefix_with_len(self.payout_currency_conf) \
                         + self.signed_payout_conf \
                         + prefix_with_len(self.payout_currency_derivation_path)

        for refund_payload in payloads_to_test:
            backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
            self._restart_test(backend, ex, partner)
            ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_payload)
            backend.raise_policy = RaisePolicy.RAISE_NOTHING
            rapdu = ex._exchange(Command.CHECK_REFUND_ADDRESS, payload=refund_payload)
            assert rapdu.status == Errors.INCORRECT_COMMAND_DATA
