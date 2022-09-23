from contextlib import contextmanager
from typing import Generator, Optional, Dict
from enum import IntEnum

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.error import ExceptionRAPDU

from ..ledger_test_signer import LedgerTestSigner
from ..exchange_partner_identity import ExchangePartnerIdentity

from .ethereum import ETH_PACKED_DERIVATION_PATH, ETH_CONF
from .ethereum_classic import ETC_PACKED_DERIVATION_PATH, ETC_CONF
from .litecoin import LTC_PACKED_DERIVATION_PATH, LTC_CONF
from .bitcoin import BTC_PACKED_DERIVATION_PATH, BTC_CONF
from .exchange_subcommands import SWAP_SPECS, SELL_SPECS, FUND_SPECS
from ..utils import concatenate


class Command(IntEnum):
    GET_VERSION                  = 0x02
    START_NEW_TRANSACTION        = 0x03
    SET_PARTNER_KEY              = 0x04
    CHECK_PARTNER                = 0x05
    PROCESS_TRANSACTION_RESPONSE = 0x06
    CHECK_TRANSACTION_SIGNATURE  = 0x07
    CHECK_PAYOUT_ADDRESS         = 0x08
    CHECK_REFUND_ADDRESS         = 0x09
    START_SIGNING_TRANSACTION    = 0x0A


class Rate(IntEnum):
    FIXED    = 0x00
    FLOATING = 0x01


class SubCommand(IntEnum):
    SWAP = 0x00
    SELL = 0x01
    FUND = 0x02



ERRORS = (
    ExceptionRAPDU(0x6A80, "INCORRECT_COMMAND_DATA"),
    ExceptionRAPDU(0x6A81, "DESERIALIZATION_FAILED"),
    ExceptionRAPDU(0x6A82, "WRONG_TRANSACTION_ID"),
    ExceptionRAPDU(0x6A83, "INVALID_ADDRESS"),
    ExceptionRAPDU(0x6A84, "USER_REFUSED"),
    ExceptionRAPDU(0x6A85, "INTERNAL_ERROR"),
    ExceptionRAPDU(0x6A86, "WRONG_P1"),
    ExceptionRAPDU(0x6A87, "WRONG_P2"),
    ExceptionRAPDU(0x6E00, "CLASS_NOT_SUPPORTED"),
    ExceptionRAPDU(0x6D00, "INVALID_INSTRUCTION"),
    ExceptionRAPDU(0x9D1A, "SIGN_VERIFICATION_FAIL")
)

class ExchangeClient:
    CLA = 0xE0
    def __init__(self,
                 client: BackendInterface,
                 rate: Rate,
                 subcommand: SubCommand,
                 name: str = "DefaultPartner"):
        if not isinstance(client, BackendInterface):
            raise TypeError('client must be an instance of BackendInterface')
        if not isinstance(rate, Rate):
            raise TypeError('rate must be an instance of Rate')
        if not isinstance(subcommand, SubCommand):
            raise TypeError('subcommand must be an instance of SubCommand')

        self._ledger_test_signer = LedgerTestSigner()
        self._fake_ledger_test_signer = LedgerTestSigner(use_test_key = False)

        self._client = client
        self._rate = rate
        self._subcommand = subcommand
        self._transaction_id: Optional[bytes] = None
        self._transaction: bytes = b""
        self._payout_currency: str = ""
        self._refund_currency: Optional[str] = None

        if self._subcommand == SubCommand.SWAP:
            self.subcommand_specs = SWAP_SPECS
        elif self._subcommand == SubCommand.SELL:
            self.subcommand_specs = SELL_SPECS
        elif self._subcommand == SubCommand.FUND:
            self.subcommand_specs = FUND_SPECS

        self._exchange_partner = ExchangePartnerIdentity(self.subcommand_specs.curve, name)
        self._fake_exchange_partner = ExchangePartnerIdentity(self.subcommand_specs.curve, name)

    @property
    def rate(self) -> Rate:
        return self._rate

    @property
    def subcommand(self) -> SubCommand:
        return self._subcommand

    @property
    def transaction_id(self) -> bytes:
        return self._transaction_id or b""

    def _exchange(self, ins: int, payload: bytes = b"") -> RAPDU:
        return self._client.exchange(self.CLA, ins, p1=self.rate,
                                     p2=self.subcommand, data=payload)

    @contextmanager
    def _exchange_async(self, ins: int, payload: bytes = b"") -> Generator[RAPDU, None, None]:
        with self._client.exchange_async(self.CLA, ins, p1=self.rate,
                                         p2=self.subcommand, data=payload) as response:
            yield response

    def get_version(self) -> RAPDU:
        return self._exchange(Command.GET_VERSION)

    def init_transaction(self) -> RAPDU:
        response = self._exchange(Command.START_NEW_TRANSACTION)
        self._transaction_id = response.data
        return response

    def set_partner_key(self, use_main_partner: bool = True) -> RAPDU:
        if use_main_partner:
            return self._exchange(Command.SET_PARTNER_KEY, self._exchange_partner.credentials)
        else:
            return self._exchange(Command.SET_PARTNER_KEY, self._fake_exchange_partner.credentials)

    def check_partner_key(self, use_test_key: bool = True) -> RAPDU:
        if use_test_key:
            signed_credentials = self._ledger_test_signer.sign(self._exchange_partner.credentials)
        else:
            signed_credentials = self._fake_ledger_test_signer.sign(self._exchange_partner.credentials)
        return self._exchange(Command.CHECK_PARTNER, signed_credentials)

    def process_transaction(self, conf: Dict, fees: bytes) -> RAPDU:
        assert self.subcommand_specs.check_conf(conf)

        self._transaction = self.subcommand_specs.create_transaction(conf, self.transaction_id)

        self._payout_currency = conf[self.subcommand_specs.payout_field]
        if self.subcommand_specs.refund_field:
            self._refund_currency = conf[self.subcommand_specs.refund_field]

        payload = concatenate(self._transaction, fees)
        return self._exchange(Command.PROCESS_TRANSACTION_RESPONSE, payload=payload)

    def check_transaction(self, use_main_partner: bool = True) -> RAPDU:
        formated_transaction = self.subcommand_specs.format_transaction(self._transaction)
        if use_main_partner:
            signed_transaction = self._exchange_partner.sign(formated_transaction)
        else:
            signed_transaction = self._fake_exchange_partner.sign(formated_transaction)
        encoded_transaction = self.subcommand_specs.encode_signature(signed_transaction)

        return self._exchange(Command.CHECK_TRANSACTION_SIGNATURE, payload=encoded_transaction)

    def _ticker_to_coin_payload(self, ticker, use_test_key) -> bytes:
        ticker_to_conf = {
            "ETC": (ETC_CONF, ETC_PACKED_DERIVATION_PATH),
            "ETH": (ETH_CONF, ETH_PACKED_DERIVATION_PATH),
            "BTC": (BTC_CONF, BTC_PACKED_DERIVATION_PATH),
            "LTC": (LTC_CONF, LTC_PACKED_DERIVATION_PATH),
        }
        assert ticker.upper() in ticker_to_conf
        conf, derivation_path = ticker_to_conf[ticker.upper()]
        if use_test_key:
            signature = self._ledger_test_signer.sign(conf)
        else:
            signature = self._fake_ledger_test_signer.sign(conf)
        return concatenate(conf) + signature + concatenate(derivation_path)

    def check_address(self, right_clicks: int, accept: bool = True, use_test_key_for_payout: bool = True, use_test_key_for_refund: bool = True) -> RAPDU:
        command = Command.CHECK_PAYOUT_ADDRESS
        payload = self._ticker_to_coin_payload(self._payout_currency, use_test_key_for_payout)

        if self._refund_currency:
            # If refund adress has to be checked, send CHECk_PAYOUT_ADDRESS first
            rapdu = self._exchange(command, payload=payload)
            if rapdu.status != 0x9000:
                return rapdu
            command = Command.CHECK_REFUND_ADDRESS
            payload = self._ticker_to_coin_payload(self._refund_currency, use_test_key_for_refund)

        with self._exchange_async(command, payload=payload):
            for _ in range(right_clicks):
                self._client.right_click()
            if not accept:
                self._client.right_click()
            self._client.both_click()

        return self._client.last_async_response

    def start_signing_transaction(self) -> RAPDU:
        return self._exchange(Command.START_SIGNING_TRANSACTION)
