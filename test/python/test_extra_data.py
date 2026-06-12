import pytest
from dataclasses import dataclass
from ragger.utils import prefix_with_len
from ragger.error import ExceptionRAPDU
from typing import Optional

from exchange_client.client import ExchangeClient, Rate, SubCommand, Errors, PayinExtraDataID
from apps.litecoin import LitecoinClient

from exchange_client.signing_authority import SigningAuthority, LEDGER_SIGNER
from exchange_client.transaction_builder import get_partner_curve, craft_and_sign_tx, ALL_SUBCOMMANDS, get_credentials
from apps import cal as cal

CURRENCY_FROM = cal.BTC_CURRENCY_CONFIGURATION
CURRENCY_TO = cal.ETH_CURRENCY_CONFIGURATION

@dataclass
class ConfForTest:
    payin_extra_id: Optional[str]
    payin_extra_data: Optional[bytes]
    valid: bool


class TestExtraData:

    @pytest.mark.parametrize('configurations', [
        # Having both is not allowed
        ConfForTest(payin_extra_id="abcdefghijklmnopqrs",
                    payin_extra_data=bytes.fromhex("01000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"),
                    valid=False),
        # Having both is not allowed
        ConfForTest(payin_extra_id="a",
                    payin_extra_data=bytes.fromhex("0000"),
                    valid=False),
        # Having both is not allowed
        ConfForTest(payin_extra_id="a",
                    payin_extra_data=bytes.fromhex("01"),
                    valid=False),
        # Having neither is allowed
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=None,
                    valid=True),
        # Having only one is allowed
        ConfForTest(payin_extra_id="abcdefghijklmnopqrs",
                    payin_extra_data=None,
                    valid=True),
        # Having only one is allowed (except for NanoS)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=bytes.fromhex("01000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"),
                    valid=True),
        # payin_extra_data with only NATIVE inside does not count as being used
        ConfForTest(payin_extra_id="abcdefghijklmnopqrs",
                    payin_extra_data=bytes.fromhex("00"),
                    valid=True),
    ])
    def test_extra_data_and_or_extra_id(self, backend, configurations):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP_NG)
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP_NG), name="Default name")

        transaction_id = ex.init_transaction().data
        credentials = get_credentials(SubCommand.SWAP_NG, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx_infos = {
            "payin_address": "LKY4hyq7ucxtdGoQ6ajkwv4ddTNA4WpYhF",
            "refund_address": "MJovkMvQ2rXXUj7TGVvnQyVMWghSdqZsmu",
            "payout_address": "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
            "refund_extra_id": "",
            "payout_extra_id": "",
            "currency_from": CURRENCY_FROM.ticker,
            "currency_to": CURRENCY_TO.ticker,
            "amount_to_provider": b"\010T2V",
            "amount_to_wallet": b"\246\333t\233+\330\000",
        }
        if configurations.payin_extra_id is not None:
            tx_infos["payin_extra_id"] = configurations.payin_extra_id
        if configurations.payin_extra_data is not None:
            tx_infos["payin_extra_data"] = configurations.payin_extra_data

        fees = 339

        tx, _ = craft_and_sign_tx(SubCommand.SWAP_NG, tx_infos, transaction_id, fees, partner)

        if configurations.valid:
            ex.process_transaction(tx)
        else:
            with pytest.raises(ExceptionRAPDU) as e:
                ex.process_transaction(tx)
            assert e.value.status == Errors.WRONG_EXTRA_ID_OR_EXTRA_DATA

    @pytest.mark.parametrize('configurations', [
        # Valid SOL_TEMPLATE: type 0x03 with 32 + 4 bytes payload (total 37 bytes)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.SOL_TEMPLATE.to_bytes(1, byteorder='big') + bytes([0x0F] * 36),
                    valid=True),
        # Invalid SOL_TEMPLATE: type 0x03 with wrong size (8 bytes payload instead of 36)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.SOL_TEMPLATE.to_bytes(1, byteorder='big') + bytes([0x0F] * 8),
                    valid=False),
        # Invalid SOL_TEMPLATE: type 0x03 with wrong size (32 bytes payload instead of 36)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.SOL_TEMPLATE.to_bytes(1, byteorder='big') + bytes([0x0F] * 32),
                    valid=False),
        # Invalid SOL_TEMPLATE: type 0x03 with wrong size (no payload)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.SOL_TEMPLATE.to_bytes(1, byteorder='big'),
                    valid=False),
        # Valid EVM_CALLDATA: type 0x01 with 32 bytes payload (total 33 bytes)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.EVM_CALLDATA.to_bytes(1, byteorder='big') + bytes([0x0F] * 32),
                    valid=True),
        # Invalid EVM_CALLDATA: type 0x01 with wrong size (31 bytes payload instead of 32)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.EVM_CALLDATA.to_bytes(1, byteorder='big') + bytes([0x0F] * 31),
                    valid=False),
        # Invalid EVM_CALLDATA: type 0x01 with wrong size (8 bytes payload instead of 32)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.EVM_CALLDATA.to_bytes(1, byteorder='big') + bytes([0x0F] * 8),
                    valid=False),
        # Valid OP_RETURN: type 0x02 with 32 bytes payload (total 33 bytes)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.OP_RETURN.to_bytes(1, byteorder='big') + bytes([0x0F] * 32),
                    valid=True),
        # Invalid OP_RETURN: type 0x02 with wrong size (31 bytes payload instead of 32)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.OP_RETURN.to_bytes(1, byteorder='big') + bytes([0x0F] * 31),
                    valid=False),
        # Invalid OP_RETURN: type 0x02 with wrong size (8 bytes payload instead of 32)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.OP_RETURN.to_bytes(1, byteorder='big') + bytes([0x0F] * 8),
                    valid=False),
        # Valid NATIVE: type 0x00 with no payload (total 1 byte)
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.NATIVE.to_bytes(1, byteorder='big'),
                    valid=True),
        # Invalid NATIVE: type 0x00 with extra bytes
        ConfForTest(payin_extra_id=None,
                    payin_extra_data=PayinExtraDataID.NATIVE.to_bytes(1, byteorder='big') + bytes([0x0F] * 1),
                    valid=False),
    ])
    def test_extra_data_size_validation(self, backend, configurations):
        ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP_NG)
        partner = SigningAuthority(curve=get_partner_curve(SubCommand.SWAP_NG), name="Default name")

        transaction_id = ex.init_transaction().data
        credentials = get_credentials(SubCommand.SWAP_NG, partner)
        ex.set_partner_key(credentials)
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
        tx_infos = {
            "payin_address": "LKY4hyq7ucxtdGoQ6ajkwv4ddTNA4WpYhF",
            "refund_address": "MJovkMvQ2rXXUj7TGVvnQyVMWghSdqZsmu",
            "payout_address": "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
            "refund_extra_id": "",
            "payout_extra_id": "",
            "currency_from": CURRENCY_FROM.ticker,
            "currency_to": CURRENCY_TO.ticker,
            "amount_to_provider": b"\010T2V",
            "amount_to_wallet": b"\246\333t\233+\330\000",
        }
        if configurations.payin_extra_id is not None:
            tx_infos["payin_extra_id"] = configurations.payin_extra_id
        if configurations.payin_extra_data is not None:
            tx_infos["payin_extra_data"] = configurations.payin_extra_data

        fees = 339

        tx, _ = craft_and_sign_tx(SubCommand.SWAP_NG, tx_infos, transaction_id, fees, partner)

        if configurations.valid:
            ex.process_transaction(tx)
        else:
            with pytest.raises(ExceptionRAPDU) as e:
                ex.process_transaction(tx)
            assert e.value.status == Errors.WRONG_EXTRA_ID_OR_EXTRA_DATA
