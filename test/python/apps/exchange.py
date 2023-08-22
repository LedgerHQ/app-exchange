from contextlib import contextmanager
from typing import Generator, Optional, Dict
from enum import IntEnum

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.utils import prefix_with_len

from ..utils import handle_lib_call_start_or_stop, int_to_minimally_sized_bytes
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
    WRONG_P2                = 0x6A87
    CLASS_NOT_SUPPORTED     = 0x6E00
    INVALID_INSTRUCTION     = 0x6D00
    SIGN_VERIFICATION_FAIL  = 0x9D1A


def prefix_with_len_custom(to_prefix: bytes, prefix_length: int = 1) -> bytes:
    prefix = len(to_prefix).to_bytes(prefix_length, byteorder="big")
    print(prefix.hex())
    b = prefix + to_prefix
    # b = b'\0' + b
    return b


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

    def process_transaction(self, transaction: bytes, fees: int) -> RAPDU:
        fees_bytes = int_to_minimally_sized_bytes(fees)
        prefix_length = 2 if (self.subcommand == SubCommand.SWAP_NG or self.subcommand == SubCommand.FUND_NG or self.subcommand == SubCommand.SELL_NG) else 1
        payload = prefix_with_len_custom(transaction, prefix_length) + prefix_with_len(fees_bytes)

        if self.subcommand == SubCommand.SWAP or self.subcommand == SubCommand.FUND or self.subcommand == SubCommand.SELL:
            return self._exchange(Command.PROCESS_TRANSACTION_RESPONSE, payload=payload)

        else:
            print(len(payload))
            print(payload.hex())
            payload_splited = [payload[x:x + MAX_CHUNK_SIZE] for x in range(0, len(payload), MAX_CHUNK_SIZE)]
            for i, p in enumerate(payload_splited):
                p2 = self.subcommand
                # Send all chunks with P2_MORE except for the last chunk
                if i != len(payload_splited) - 1:
                    p2 |= P2_MORE
                # Send all chunks with P2_EXTEND except for the first chunk
                if i != 0:
                    p2 |= P2_EXTEND
                rapdu = self._client.exchange(self.CLA, Command.PROCESS_TRANSACTION_RESPONSE, p1=self.rate, p2=p2, data=p)

        return rapdu

    def check_transaction_signature(self, encoded_transaction: bytes) -> RAPDU:
        return self._exchange(Command.CHECK_TRANSACTION_SIGNATURE, payload=encoded_transaction)

    @contextmanager
    def check_address(self,
                      payout_configuration: bytes,
                      refund_configuration: Optional[bytes] = None) -> Generator[None, None, None]:
        self._premature_error=False

        if self._subcommand == SubCommand.SWAP or self._subcommand == SubCommand.SWAP_NG:
            assert refund_configuration != None, f'A refund currency is needed but no conf as been given'
            # If refund adress has to be checked, send sync CHECk_PAYOUT_ADDRESS first
            rapdu = self._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_configuration)
            if rapdu.status != 0x9000:
                self._premature_error = True
                self._check_address_result = rapdu
                yield rapdu
            else:
                with self._exchange_async(Command.CHECK_REFUND_ADDRESS, payload=refund_configuration) as response:
                    yield response
        else:
            with self._exchange_async(Command.CHECK_PAYOUT_ADDRESS, payload=payout_configuration) as response:
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
