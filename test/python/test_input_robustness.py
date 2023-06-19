from ragger.utils import RAPDU, prefix_with_len, create_currency_config
from ragger.backend import RaisePolicy
from ragger.navigator import NavInsID

from .utils import ROOT_SCREENSHOT_PATH
from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors, TICKER_TO_CONF, TICKER_TO_PACKED_DERIVATION_PATH, Command
from .apps.bsc import BSC_CONF, BSC_CONF_ALIAS_1, BSC_CONF_ALIAS_2, BSC_PACKED_DERIVATION_PATH
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

    def test_robustness_check_payout_address(self, backend):
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

    def test_robustness_check_refund_address(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

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

    def test_robustness_coin_configuration(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

        currency_conf_to_test = (
            # Ticker missing
            create_currency_config("", "ethereum"),
            # Ticker too small
            create_currency_config("A", "ethereum"),
            # Ticker too long
            create_currency_config("abcdefghij", "ethereum"),
            # Appname missing
            create_currency_config("ETH", ""),
            # Appname too small
            create_currency_config("ETH", "ab"),
            # Appname too small
            create_currency_config("ETH", "abcdefghijklmnopqrstuvwxyz0123456"),
        )

        for conf in currency_conf_to_test:
            backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
            self._restart_test(backend, ex, partner)
            payload = prefix_with_len(conf) + LEDGER_SIGNER.sign(conf) + prefix_with_len(self.payout_currency_derivation_path)
            backend.raise_policy = RaisePolicy.RAISE_NOTHING
            rapdu = ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payload)
            assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

    def test_currency_normalization(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=ex.partner_curve, name="Default name")

        # This tickers should be normalized and accepted
        payout_currency_conf_to_test = (
            create_currency_config("eth", "Ethereum", ("ETH", 18)),
            create_currency_config("Eth", "Ethereum", ("ETH", 18)),
        )
        refund_currency_conf_to_test = (
            create_currency_config("xlm", "Stellar"),
            create_currency_config("xLm", "Stellar"),
        )

        for payout_conf in payout_currency_conf_to_test:
            for refund_conf in refund_currency_conf_to_test:
                payout_payload = prefix_with_len(payout_conf) + LEDGER_SIGNER.sign(payout_conf) + prefix_with_len(self.payout_currency_derivation_path)
                refund_payload = prefix_with_len(refund_conf) + LEDGER_SIGNER.sign(refund_conf) + prefix_with_len(self.refund_currency_derivation_path)

                backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
                self._restart_test(backend, ex, partner)
                ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_payload)
                backend.raise_policy = RaisePolicy.RAISE_NOTHING
                rapdu = ex._exchange(Command.CHECK_REFUND_ADDRESS, payload=refund_payload)
                # The address is false on purpose to prevent from having to handle the UI
                # What we want to test is before the actual address check by Stellar
                assert rapdu.status == Errors.INVALID_ADDRESS

        # This time the tickers must not match with the conf given in tx_infos
        currency_conf_to_test = (
            create_currency_config("XLMm", "Stellar"),
            create_currency_config("XL ", "Stellar"),
            create_currency_config("XL", "Stellar"),
        )
        for conf in currency_conf_to_test:
            self._restart_test(backend, ex, partner)
            ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_payload)
            payload = prefix_with_len(conf) + LEDGER_SIGNER.sign(conf) + prefix_with_len(self.refund_currency_derivation_path)
            backend.raise_policy = RaisePolicy.RAISE_NOTHING
            rapdu = ex._exchange(Command.CHECK_REFUND_ADDRESS, payload=payload)
            assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

def test_currency_normalization_fund(backend, navigator, test_name):
    tx_infos = {
        "user_id": "Jon Wick",
        "account_name": "My account 00",
        "in_currency": "XLM",
        "in_amount": int.to_bytes(10000000, length=4, byteorder='big'),
        "in_address": "GB5ZQJYKSZP3JOMOCWCBI7SPQUBW6ZL3642FUB7IYNAOC2EQMAFXI3P2",
    }
    fees = 100
    currency_conf_to_test = (
        create_currency_config("xlm", "Stellar"),
        create_currency_config("xLm", "Stellar"),
    )

    for conf in currency_conf_to_test:
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.FUND)
        partner = SigningAuthority(curve=ex.partner_curve, name="Default name")
        ex.init_transaction()
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        fees_bytes = int.to_bytes(fees, length=4, byteorder='big')
        ex.process_transaction(tx_infos, fees_bytes)
        ex.check_transaction_signature(partner)

        payload = prefix_with_len(conf) + LEDGER_SIGNER.sign(conf) + prefix_with_len(BSC_PACKED_DERIVATION_PATH)
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        with ex._exchange_async(Command.CHECK_PAYOUT_ADDRESS, payload=payload):
            navigator.navigate_until_text_and_compare(NavInsID.RIGHT_CLICK,
                                                      [NavInsID.BOTH_CLICK],
                                                      "Accept",
                                                      ROOT_SCREENSHOT_PATH,
                                                      test_name)

class TestAliasAppname:
    tx_infos = {
        "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
        "payin_extra_id": b"",
        "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "refund_extra_id": b"",
        "payout_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
        "payout_extra_id": b"",
        "currency_from": "ETH",
        "currency_to": "BSC",
        "amount_to_provider": int.to_bytes(1000, length=8, byteorder='big'),
        "amount_to_wallet": b"\246\333t\233+\330\000",
    }
    fees_bytes = int.to_bytes(100, length=4, byteorder='big')

    def test_currency_alias(self, backend):
        for conf in BSC_CONF, BSC_CONF_ALIAS_1, BSC_CONF_ALIAS_2:
            ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
            partner = SigningAuthority(curve=ex.partner_curve, name="Default name")
            ex.init_transaction()
            ex.set_partner_key(partner.credentials)
            ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
            ex.process_transaction(self.tx_infos, self.fees_bytes)
            ex.check_transaction_signature(partner)

            # If the alias does not work, CHECK_PAYOUT_ADDRESS will crash
            payload = prefix_with_len(conf) + LEDGER_SIGNER.sign(conf) + prefix_with_len(BSC_PACKED_DERIVATION_PATH)
            ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payload)
