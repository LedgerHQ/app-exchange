from contextlib import contextmanager
from typing import Generator, Optional, Dict
from enum import IntEnum

from ragger.backend.interface import BackendInterface, RAPDU

from ..utils import handle_lib_call_start_or_stop, int_to_minimally_sized_bytes, prefix_with_len_custom
from .exchange_transaction_builder import SubCommand

MAX_CHUNK_SIZE = 255

P2_EXTEND = 0x01 << 4
P2_MORE   = 0x02 << 4


class Command(IntEnum):
    GET_VERSION                  = 0x02
    START_NEW_TRANSACTION        = 0x03
    SET_PARTNER_KEY              = 0x04
    CHECK_PARTNER                = 0x05
    PROCESS_TRANSACTION_RESPONSE = 0x06
    CHECK_TRANSACTION_SIGNATURE  = 0x07
    CHECK_PAYOUT_ADDRESS         = 0x08
    CHECK_ASSET_IN_LEGACY        = 0x08
    CHECK_ASSET_IN               = 0x0B
    CHECK_REFUND_ADDRESS         = 0x09
    START_SIGNING_TRANSACTION    = 0x0A


class Rate(IntEnum):
    FIXED    = 0x00
    FLOATING = 0x01


class Errors(IntEnum):
    INCORRECT_COMMAND_DATA  = 0x6A80
    DESERIALIZATION_FAILED  = 0x6A81
    WRONG_TRANSACTION_ID    = 0x6A82
    INVALID_ADDRESS         = 0x6A83
    USER_REFUSED            = 0x6A84
    INTERNAL_ERROR          = 0x6A85
    WRONG_P1                = 0x6A86
    WRONG_P2_SUBCOMMAND     = 0x6A87
    WRONG_P2_EXTENSION      = 0x6A88
    INVALID_P2_EXTENSION    = 0x6A89
    CLASS_NOT_SUPPORTED     = 0x6E00
    MALFORMED_APDU          = 0x6E01
    INVALID_DATA_LENGTH     = 0x6E02
    INVALID_INSTRUCTION     = 0x6D00
    UNEXPECTED_INSTRUCTION  = 0x6D01
    SIGN_VERIFICATION_FAIL  = 0x9D1A
    SUCCESS                 = 0x9000


EXCHANGE_CLASS = 0xE0

class ExchangeClient:
    CLA = EXCHANGE_CLASS
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

    @property
    def rate(self) -> Rate:
        return self._rate

    @property
    def subcommand(self) -> SubCommand:
        return self._subcommand

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
        return response

    def set_partner_key(self, credentials: bytes) -> RAPDU:
        return self._exchange(Command.SET_PARTNER_KEY, credentials)

    def check_partner_key(self, signed_credentials: bytes) -> RAPDU:
        return self._exchange(Command.CHECK_PARTNER, signed_credentials)

    def process_transaction(self, transaction: bytes) -> RAPDU:
        if self.subcommand == SubCommand.SWAP or self.subcommand == SubCommand.FUND or self.subcommand == SubCommand.SELL:
            return self._exchange(Command.PROCESS_TRANSACTION_RESPONSE, payload=transaction)

        else:
            payload_split = [transaction[x:x + MAX_CHUNK_SIZE] for x in range(0, len(transaction), MAX_CHUNK_SIZE)]
            for i, p in enumerate(payload_split):
                p2 = self.subcommand
                # Send all chunks with P2_MORE except for the last chunk
                if i != len(payload_split) - 1:
                    p2 |= P2_MORE
                # Send all chunks with P2_EXTEND except for the first chunk
                if i != 0:
                    p2 |= P2_EXTEND
                rapdu = self._client.exchange(self.CLA, Command.PROCESS_TRANSACTION_RESPONSE, p1=self.rate, p2=p2, data=p)

        return rapdu

    def check_transaction_signature(self, encoded_transaction: bytes) -> RAPDU:
        return self._exchange(Command.CHECK_TRANSACTION_SIGNATURE, payload=encoded_transaction)

    def check_payout_address(self, payout_configuration: bytes) -> RAPDU:
        return self._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_configuration)

    @contextmanager
    def check_refund_address(self, refund_configuration) -> Generator[None, None, None]:
        with self._exchange_async(Command.CHECK_REFUND_ADDRESS, payload=refund_configuration) as response:
            yield response

    @contextmanager
    def check_asset_in(self, payout_configuration: bytes) -> Generator[None, None, None]:
        if self._subcommand == SubCommand.SELL or self._subcommand == SubCommand.FUND:
            ins = Command.CHECK_ASSET_IN_LEGACY
        else:
            ins = Command.CHECK_ASSET_IN
        with self._exchange_async(ins, payload=payout_configuration) as response:
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
            handle_lib_call_start_or_stop(self._client)
        return rapdu
