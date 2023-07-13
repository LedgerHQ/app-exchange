from ragger.utils import RAPDU, prefix_with_len, create_currency_config
from ragger.backend import RaisePolicy

from .apps.exchange import ExchangeClient, Rate, SubCommand, Errors, Command
from .apps.exchange_transaction_builder import get_partner_curve, craft_tx, encode_tx
from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER
from .apps import cal as cal


class TestRobustnessSET_PARTNER_KEY:

    def test_robustness_set_partner_key_name_too_long(self, backend):
        name = "PARTNER_NAME_123" # Too long
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP), name=name)

        ex.init_transaction()
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.set_partner_key(partner.credentials)
        assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

    def test_robustness_set_partner_key_name_too_short(self, backend):
        name = "PA" # Too short
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP), name=name)

        ex.init_transaction()
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        rapdu: RAPDU = ex.set_partner_key(partner.credentials)
        assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

    def test_robustness_set_partner_key_name_none(self, backend):
        name = "" # Nothing
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP), name=name)

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
    fees = 100

    def _restart_test(self, backend, ex):
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP), name="Default name")
        transaction_id = ex.init_transaction().data
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        tx = craft_tx(SubCommand.SWAP, self.tx_infos, transaction_id)
        ex.process_transaction(tx, self.fees)
        encoded_tx = encode_tx(SubCommand.SWAP, partner, tx)
        ex.check_transaction_signature(encoded_tx)

    def test_robustness_check_payout_address(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)

        payout_currency_conf = cal.get_currency_conf(self.tx_infos["currency_to"])
        signed_payout_conf = cal.sign_currency_conf(payout_currency_conf)
        payout_currency_derivation_path = cal.get_derivation_path(self.tx_infos["currency_to"])
        refund_currency_conf = cal.get_currency_conf(self.tx_infos["currency_from"])
        signed_refund_conf = cal.sign_currency_conf(refund_currency_conf)
        refund_currency_derivation_path = cal.get_derivation_path(self.tx_infos["currency_from"])

        payloads_to_test = (
            # Nothing
            b'',
            # Empty payout_currency_conf
            prefix_with_len(b'') + signed_payout_conf + prefix_with_len(payout_currency_derivation_path),
            # No signed_payout_conf
            prefix_with_len(payout_currency_conf) + b'' + prefix_with_len(payout_currency_derivation_path),
            # Empty payout_currency_derivation_path
            prefix_with_len(payout_currency_conf) + signed_payout_conf + prefix_with_len(b''),
            # Trailing bytes
            prefix_with_len(payout_currency_conf) + signed_payout_conf + prefix_with_len(payout_currency_derivation_path) + b"a",
        )

        for payout_payload in payloads_to_test:
            backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
            self._restart_test(backend, ex)
            backend.raise_policy = RaisePolicy.RAISE_NOTHING
            rapdu = ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_payload)
            assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

    def test_robustness_check_refund_address(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)

        payout_currency_conf = cal.get_currency_conf(self.tx_infos["currency_to"])
        signed_payout_conf = cal.sign_currency_conf(payout_currency_conf)
        payout_currency_derivation_path = cal.get_derivation_path(self.tx_infos["currency_to"])
        refund_currency_conf = cal.get_currency_conf(self.tx_infos["currency_from"])
        signed_refund_conf = cal.sign_currency_conf(refund_currency_conf)
        refund_currency_derivation_path = cal.get_derivation_path(self.tx_infos["currency_from"])

        payloads_to_test = (
            # Nothing
            b'',
            # Empty refund_currency_conf
            prefix_with_len(b'') + signed_refund_conf + prefix_with_len(refund_currency_derivation_path),
            # No signed_refund_conf
            prefix_with_len(refund_currency_conf) + b'' + prefix_with_len(refund_currency_derivation_path),
            # Empty refund_currency_derivation_path
            prefix_with_len(refund_currency_conf) + signed_refund_conf + prefix_with_len(b''),
            # Trailing bytes
            prefix_with_len(refund_currency_conf) + signed_refund_conf + prefix_with_len(refund_currency_derivation_path) + b"a",
        )
        payout_payload = prefix_with_len(payout_currency_conf) \
                         + signed_payout_conf \
                         + prefix_with_len(payout_currency_derivation_path)

        for refund_payload in payloads_to_test:
            backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
            self._restart_test(backend, ex)
            ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_payload)
            backend.raise_policy = RaisePolicy.RAISE_NOTHING
            rapdu = ex._exchange(Command.CHECK_REFUND_ADDRESS, payload=refund_payload)
            assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

    def test_robustness_coin_configuration(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)

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
            self._restart_test(backend, ex)
            payload = prefix_with_len(conf) + cal.sign_currency_conf(conf) + prefix_with_len(cal.get_derivation_path(self.tx_infos["currency_to"]))
            backend.raise_policy = RaisePolicy.RAISE_NOTHING
            rapdu = ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payload)
            assert rapdu.status == Errors.INCORRECT_COMMAND_DATA

    def test_currency_normalization_correct(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)

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
                payout_payload = prefix_with_len(payout_conf) + cal.sign_currency_conf(payout_conf) + prefix_with_len(cal.get_derivation_path(self.tx_infos["currency_to"]))
                refund_payload = prefix_with_len(refund_conf) + cal.sign_currency_conf(refund_conf) + prefix_with_len(cal.get_derivation_path(self.tx_infos["currency_from"]))

                backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
                self._restart_test(backend, ex)
                ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_payload)
                backend.raise_policy = RaisePolicy.RAISE_NOTHING
                rapdu = ex._exchange(Command.CHECK_REFUND_ADDRESS, payload=refund_payload)
                # The address is false on purpose to prevent from having to handle the UI
                # What we want to test is before the actual address check by Stellar
                assert rapdu.status == Errors.INVALID_ADDRESS

    def test_currency_normalization_incorrect(self, backend):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)

        # This time the tickers must not match with the conf given in tx_infos
        currency_conf_to_test = (
            create_currency_config("Ethh", "Ethereum"),
            create_currency_config("ET ", "Ethereum"),
            create_currency_config("XLM", "Ethereum"),
        )
        for conf in currency_conf_to_test:
            backend.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
            self._restart_test(backend, ex)
            payout_payload = prefix_with_len(conf) + cal.sign_currency_conf(conf) + prefix_with_len(cal.get_derivation_path(self.tx_infos["currency_to"]))
            backend.raise_policy = RaisePolicy.RAISE_NOTHING
            rapdu = ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_payload)
            assert rapdu.status == Errors.INCORRECT_COMMAND_DATA


def test_currency_normalization_fund(backend, exchange_navigation_helper):
    partner = SigningAuthority(curve=get_partner_curve(SubCommand.FUND), name="Default name")
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
        transaction_id = ex.init_transaction().data
        ex.set_partner_key(partner.credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
        tx = craft_tx(SubCommand.FUND, tx_infos, transaction_id)
        ex.process_transaction(tx, fees)
        encoded_tx = encode_tx(SubCommand.FUND, partner, tx)
        ex.check_transaction_signature(encoded_tx)

        payload = prefix_with_len(conf) + cal.sign_currency_conf(conf) + prefix_with_len(cal.get_derivation_path(tx_infos["in_currency"]))
        backend.raise_policy = RaisePolicy.RAISE_NOTHING
        with ex._exchange_async(Command.CHECK_PAYOUT_ADDRESS, payload=payload):
            exchange_navigation_helper.simple_accept()


class TestAliasAppname:

    def test_currency_alias(self, backend):
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP), name="Default name")
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
        fees = 100

        bsc_conf = cal.get_currency_conf(tx_infos["currency_to"]) # "Binance Smart Chain"
        bsc_conf_alias_1 = create_currency_config("BSC", "bsc", ("BSC", 12))
        bsc_conf_alias_2 = create_currency_config("BSC", "Bsc", ("BSC", 12))
        for conf in bsc_conf, bsc_conf_alias_1, bsc_conf_alias_2:
            ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
            transaction_id = ex.init_transaction().data
            ex.set_partner_key(partner.credentials)
            ex.check_partner_key(LEDGER_SIGNER.sign(partner.credentials))
            tx = craft_tx(SubCommand.SWAP, tx_infos, transaction_id)
            ex.process_transaction(tx, fees)
            encoded_tx = encode_tx(SubCommand.SWAP, partner, tx)
            ex.check_transaction_signature(encoded_tx)

            # If the alias does not work, CHECK_PAYOUT_ADDRESS will crash
            payload = prefix_with_len(conf) + LEDGER_SIGNER.sign(conf) + prefix_with_len(cal.get_derivation_path(tx_infos["currency_to"]))
            ex._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payload)
