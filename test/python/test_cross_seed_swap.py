# import pytest

# from ragger.utils import RAPDU, prefix_with_len, create_currency_config
# from ragger.error import ExceptionRAPDU

# from ledger_app_clients.exchange.client import ExchangeClient, Rate, SubCommand, Errors, Command, P2_EXTEND, P2_MORE, EXCHANGE_CLASS
# from ledger_app_clients.exchange.transaction_builder import get_partner_curve, LEGACY_SUBCOMMANDS, ALL_SUBCOMMANDS, NEW_SUBCOMMANDS, get_credentials, craft_and_sign_tx
# from ledger_app_clients.exchange.signing_authority import SigningAuthority, LEDGER_SIGNER
# from .apps import cal as cal
# from .apps.ethereum import ETC_PACKED_DERIVATION_PATH

# CURRENCY_TO = cal.BTC_CURRENCY_CONFIGURATION
# CURRENCY_FROM = cal.ETH_CURRENCY_CONFIGURATION

# # Some valid infos for TX. Content is irrelevant for the test

# SWAP_TX_INFOS = {
#      "payin_address": b"0xd692Cb1346262F584D17B4B470954501f6715a82",
#      "payin_extra_id": b"",
#      "refund_address": b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
#      "refund_extra_id": b"",
#      "payout_address": b"bc1qqtl9jlrwcr3fsfcjj2du7pu6fcgaxl5dsw2vyg",
#      "payout_extra_id": b"",
#      "currency_from": CURRENCY_FROM.ticker,
#      "currency_to": CURRENCY_TO.ticker,
#      "amount_to_provider": bytes.fromhex("013fc3a717fb5000"),
#      "amount_to_wallet": b"\x0b\xeb\xc2\x00",
# }
# FEES = 100

# class TestCrossSeedSwap:

#     def _init_test(self, backend, wrong_refund=False, wrong_payout=False):
#         ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP_NG)
#         partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP_NG), name="Name")
#         transaction_id = ex.init_transaction().data
#         credentials = get_credentials(SubCommand.SWAP_NG, partner)
#         ex.set_partner_key(credentials)
#         ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
#         tx_infos = SWAP_TX_INFOS.copy()
#         if wrong_refund:
#             tx_infos["refund_address"] = "abc"
#         if wrong_payout:
#             tx_infos["payout_address"] = "abc"
#         tx, tx_signature = craft_and_sign_tx(SubCommand.SWAP_NG, tx_infos, transaction_id, FEES, partner)
#         ex.process_transaction(tx)
#         ex.check_transaction_signature(tx_signature)
#         return ex

#     def test_cross_seed_swap_refund_first(self, backend, exchange_navigation_helper):
#         ex = self._init_test(backend)

#         ex.check_refund_address_no_display(CURRENCY_FROM.get_conf_for_ticker())
#         ex.check_payout_address(CURRENCY_TO.get_conf_for_ticker())

#         with ex.prompt_ui_display():
#             exchange_navigation_helper.simple_accept()

#     def test_cross_seed_swap_missing_refund(self, backend):
#         ex = self._init_test(backend)

#         # ex.check_refund_address_no_display(CURRENCY_FROM.get_conf_for_ticker())
#         ex.check_payout_address(CURRENCY_TO.get_conf_for_ticker())

#         with pytest.raises(ExceptionRAPDU) as e:
#             with ex.prompt_ui_display():
#                 pass
#         assert e.value.status == Errors.UNEXPECTED_INSTRUCTION

#     def test_cross_seed_swap_missing_payout(self, backend):
#         ex = self._init_test(backend)

#         ex.check_refund_address_no_display(CURRENCY_FROM.get_conf_for_ticker())
#         # ex.check_payout_address(CURRENCY_TO.get_conf_for_ticker())

#         with pytest.raises(ExceptionRAPDU) as e:
#             with ex.prompt_ui_display():
#                 pass
#         assert e.value.status == Errors.UNEXPECTED_INSTRUCTION

#     def test_cross_seed_swap_missing_payout_prompt_ui(self, backend):
#         ex = self._init_test(backend)

#         # ex.check_payout_address(CURRENCY_TO.get_conf_for_ticker())
#         with pytest.raises(ExceptionRAPDU) as e:
#             with ex.check_refund_address(CURRENCY_FROM.get_conf_for_ticker()):
#                 pass
#         assert e.value.status == Errors.MISSING_PAYOUT_CHECK

#     def test_cross_seed_swap_failed_refund(self, backend, exchange_navigation_helper):
#         ex = self._init_test(backend, wrong_refund=True)

#         with pytest.raises(ExceptionRAPDU) as e:
#             ex.check_refund_address_no_display(CURRENCY_FROM.get_conf_for_ticker())
#         assert e.value.status == Errors.INVALID_ADDRESS

#     def test_cross_seed_swap_failed_payout(self, backend, exchange_navigation_helper):
#         ex = self._init_test(backend, wrong_payout=True)

#         with pytest.raises(ExceptionRAPDU) as e:
#             ex.check_refund_address_no_display(CURRENCY_FROM.get_conf_for_ticker())
#         assert e.value.status == Errors.INVALID_ADDRESS
