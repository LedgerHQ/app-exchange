from contextlib import contextmanager
from typing import Generator, Optional, Dict
from enum import IntEnum
from time import sleep

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.error import ExceptionRAPDU
from ragger.utils import prefix_with_len

from ..signing_authority import SigningAuthority

from cryptography.hazmat.primitives.asymmetric import ec

from .ethereum import ETH_PACKED_DERIVATION_PATH, ETH_CONF
from .ethereum_classic import ETC_PACKED_DERIVATION_PATH, ETC_CONF
from .litecoin import LTC_PACKED_DERIVATION_PATH, LTC_CONF
from .bitcoin import BTC_PACKED_DERIVATION_PATH, BTC_CONF
from .stellar import XLM_PACKED_DERIVATION_PATH, XLM_CONF
from .solana_utils import SOL_PACKED_DERIVATION_PATH, SOL_CONF
from .xrp import XRP_PACKED_DERIVATION_PATH, XRP_CONF

from .exchange_subcommands import SWAP_SPECS, SELL_SPECS, FUND_SPECS


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


TICKER_TO_CONF = {
    "ETC": ETC_CONF,
    "ETH": ETH_CONF,
    "BTC": BTC_CONF,
    "LTC": LTC_CONF,
    "XLM": XLM_CONF,
    "SOL": SOL_CONF,
    "XRP": XRP_CONF,
}

TICKER_TO_PACKED_DERIVATION_PATH = {
    "ETC": ETC_PACKED_DERIVATION_PATH,
    "ETH": ETH_PACKED_DERIVATION_PATH,
    "BTC": BTC_PACKED_DERIVATION_PATH,
    "LTC": LTC_PACKED_DERIVATION_PATH,
    "XLM": XLM_PACKED_DERIVATION_PATH,
    "SOL": SOL_PACKED_DERIVATION_PATH,
    "XRP": XRP_PACKED_DERIVATION_PATH,
}


class Errors(IntEnum):
    INCORRECT_COMMAND_DATA  = 0x6A80
    DESERIALIZATION_FAILED  = 0x6A81
    WRONG_TRANSACTION_ID    = 0x6A82
    INVALID_ADDRESS         = 0x6A83
    USER_REFUSED            = 0x6A84
    INTERNAL_ERROR          = 0x6A85
    WRONG_P1                = 0x6A86
    WRONG_P2                = 0x6A87
    CLASS_NOT_SUPPORTED     = 0x6E00
    INVALID_INSTRUCTION     = 0x6D00
    SIGN_VERIFICATION_FAIL  = 0x9D1A


class ExchangeClient:
    CLA = 0xE0
    def __init__(self,
                 client: BackendInterface,
                 rate: Rate,
                 subcommand: SubCommand):
        if not isinstance(client, BackendInterface):
            raise TypeError('client must be an instance of BackendInterface')
        if not isinstance(rate, Rate):
            raise TypeError('rate must be an instance of Rate')
        if not isinstance(subcommand, SubCommand):
            raise TypeError('subcommand must be an instance of SubCommand')

        self._client = client
        self._rate = rate
        self._subcommand = subcommand
        self._transaction_id: Optional[bytes] = None
        self._transaction: bytes = b""
        self._payout_currency: str = ""
        self._refund_currency: Optional[str] = None

        if self._subcommand == SubCommand.SWAP:
            self._subcommand_specs = SWAP_SPECS
        elif self._subcommand == SubCommand.SELL:
            self._subcommand_specs = SELL_SPECS
        elif self._subcommand == SubCommand.FUND:
            self._subcommand_specs = FUND_SPECS

    @property
    def partner_curve(self) -> ec.EllipticCurve:
        return self._subcommand_specs.curve

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

    def set_partner_key(self, credentials: bytes) -> RAPDU:
        return self._exchange(Command.SET_PARTNER_KEY, credentials)

    def check_partner_key(self, signed_credentials: bytes) -> RAPDU:
        return self._exchange(Command.CHECK_PARTNER, signed_credentials)

    def process_transaction(self, conf: Dict, fees: bytes) -> RAPDU:
        assert self._subcommand_specs.check_conf(conf)

        self._transaction = self._subcommand_specs.create_transaction(conf, self.transaction_id)

        self._payout_currency = conf[self._subcommand_specs.payout_field]
        assert self._payout_currency.upper() in TICKER_TO_CONF, f'No conf found for payout ticker {self._payout_currency.upper()}'
        assert self._payout_currency.upper() in TICKER_TO_PACKED_DERIVATION_PATH, f'No conf found for payout ticker {self._payout_currency.upper()}'
        if self._subcommand_specs.refund_field:
            self._refund_currency = conf[self._subcommand_specs.refund_field]
            assert self._refund_currency.upper() in TICKER_TO_CONF, f'No conf found for refund ticker {self._refund_currency.upper()}'
            assert self._refund_currency.upper() in TICKER_TO_PACKED_DERIVATION_PATH, f'No conf found for refund ticker {self._refund_currency.upper()}'

        payload = prefix_with_len(self._transaction) + prefix_with_len(fees)
        return self._exchange(Command.PROCESS_TRANSACTION_RESPONSE, payload=payload)

    def check_transaction_signature(self, signer: SigningAuthority) -> RAPDU:
        formated_transaction = self._subcommand_specs.format_transaction(self._transaction)
        signed_transaction = signer.sign(formated_transaction)
        encoded_transaction = self._subcommand_specs.encode_signature(signed_transaction)
        return self._exchange(Command.CHECK_TRANSACTION_SIGNATURE, payload=encoded_transaction)

    @contextmanager
    def check_address(self, payout_signer: SigningAuthority, refund_signer: Optional[SigningAuthority] = None) -> Generator[None, None, None]:
        payout_currency_conf = TICKER_TO_CONF[self._payout_currency.upper()]
        signed_payout_conf = payout_signer.sign(payout_currency_conf)
        payout_currency_derivation_path = TICKER_TO_PACKED_DERIVATION_PATH[self._payout_currency.upper()]
        payload = prefix_with_len(payout_currency_conf) + signed_payout_conf + prefix_with_len(payout_currency_derivation_path)
        self._premature_error=False

        if self._refund_currency:
            assert refund_signer != None, f'A refund currency is specified but no SigningAuthority as been given to sign it'
            # If refund adress has to be checked, send sync CHECk_PAYOUT_ADDRESS first
            rapdu = self._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payload)
            if rapdu.status != 0x9000:
                self._premature_error = True
                self._check_address_result = rapdu
                yield rapdu
            else:
                refund_currency_conf = TICKER_TO_CONF[self._refund_currency.upper()]
                signed_refund_conf = refund_signer.sign(refund_currency_conf)
                refund_currency_derivation_path = TICKER_TO_PACKED_DERIVATION_PATH[self._refund_currency.upper()]
                payload = prefix_with_len(refund_currency_conf) + signed_refund_conf + prefix_with_len(refund_currency_derivation_path)

                with self._exchange_async(Command.CHECK_REFUND_ADDRESS, payload=payload) as response:
                    yield response
        else:
            with self._exchange_async(Command.CHECK_PAYOUT_ADDRESS, payload=payload) as response:
                yield response

    def get_check_address_response(self) -> RAPDU:
        if self._premature_error:
            return self._check_address_result
        else:
            return self._client.last_async_response

    def start_signing_transaction(self) -> RAPDU:
        rapdu = self._exchange(Command.START_SIGNING_TRANSACTION)

        # The reception of the APDU means that the Exchange app has received the request
        # and will start os_lib_call.
        # We give some time to the OS to actually process the os_lib_call
        if rapdu.status == 0x9000:
            # If the exchange app accepts starting the library app, give it time to actually start
            sleep(0.5)

            # The USB stack will be reset by the called app
            self._client.handle_usb_reset()
        return rapdu
