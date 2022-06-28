from base64 import urlsafe_b64encode
from contextlib import contextmanager
from typing import Generator, Optional, Dict
from enum import IntEnum

from ragger.backend.interface import BackendInterface, RAPDU
from ragger import ApplicationError

from ..common import LEDGER_TEST_PRIVATE_KEY

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from .ethereum import ETH_PACKED_DERIVATION_PATH, ETH_CONF, ETH_CONF_DER_SIGNATURE
from .litecoin import LTC_PACKED_DERIVATION_PATH, LTC_CONF, LTC_CONF_DER_SIGNATURE
from .bitcoin import BTC_PACKED_DERIVATION_PATH, BTC_CONF, BTC_CONF_DER_SIGNATURE
from .pb.exchange_pb2 import NewFundResponse, NewSellResponse, NewTransactionResponse
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


class SubCommand(IntEnum):
    SWAP = 0x00
    SELL = 0x01
    FUND = 0x02


class Rate(IntEnum):
    FIXED    = 0x00
    FLOATING = 0x01


ERRORS = (
    ApplicationError(0x6A80, "INCORRECT_COMMAND_DATA"),
    ApplicationError(0x6A81, "DESERIALIZATION_FAILED"),
    ApplicationError(0x6A82, "WRONG_TRANSACTION_ID"),
    ApplicationError(0x6A83, "INVALID_ADDRESS"),
    ApplicationError(0x6A84, "USER_REFUSED"),
    ApplicationError(0x6A85, "INTERNAL_ERROR"),
    ApplicationError(0x6A86, "WRONG_P1"),
    ApplicationError(0x6A87, "WRONG_P2"),
    ApplicationError(0x6E00, "CLASS_NOT_SUPPORTED"),
    ApplicationError(0x6D00, "INVALID_INSTRUCTION"),
    ApplicationError(0x9D1A, "SIGN_VERIFICATION_FAIL")
)


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
        self._partner_name: bytes = b"Default_Partner"
        self._transaction: bytes = b""
        self._payout_payload: bytes = b""
        self._refund_payload: bytes = b""
        if self._subcommand == SubCommand.SWAP:
            self._curve = ec.SECP256K1()
        else:
            self._curve = ec.SECP256R1()

    @property
    def rate(self) -> bytes:
        return self._rate

    @property
    def subcommand(self) -> bytes:
        return self._subcommand

    @property
    def transaction_id(self) -> bytes:
        return self._transaction_id or b""

    @property
    def partner_name(self) -> bytes:
        return self._partner_name

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

    def set_partner_key(self) -> RAPDU:
        self._partner_privkey = ec.generate_private_key(self._curve, backend=default_backend())
        partner_pubkey = self._partner_privkey.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        private_number = int.from_bytes(LEDGER_TEST_PRIVATE_KEY, "big")
        partner_key = ec.derive_private_key(private_value=private_number, curve=ec.SECP256K1(), backend=default_backend())
        payload = len(self.partner_name).to_bytes(1, "big") + self.partner_name + partner_pubkey
        self._signature = partner_key.sign(payload, ec.ECDSA(hashes.SHA256()))
        return self._exchange(Command.SET_PARTNER_KEY, payload)

    def check_partner_key(self) -> RAPDU:
        return self._exchange(Command.CHECK_PARTNER, self._signature)

    def _ticker_to_coin_payload(self, ticker) -> bytes:
        ticker_to_conf = {
            "ETH": (ETH_CONF, ETH_CONF_DER_SIGNATURE, ETH_PACKED_DERIVATION_PATH),
            "BTC": (BTC_CONF, BTC_CONF_DER_SIGNATURE, BTC_PACKED_DERIVATION_PATH),
            "LTC": (LTC_CONF, LTC_CONF_DER_SIGNATURE, LTC_PACKED_DERIVATION_PATH),
        }
        assert ticker in ticker_to_conf
        conf, signature, derivation_path = ticker_to_conf[ticker]
        return concatenate(conf) + signature + concatenate(derivation_path)

    def _process_transaction_payload(self, Response,
            conf: Dict, req_conf: Dict,
            do_encode: bool,
            payout_field: str, refund_field: Optional[str]) -> bytes:

        assert all(i in conf for i in req_conf)
        assert len(conf) == len(req_conf)
        pb_buffer = Response(**conf, device_transaction_id=self.transaction_id).SerializeToString()

        # preparing payload for further check step
        self._payout_payload = self._ticker_to_coin_payload(conf[payout_field])
        if refund_field:
            self._refund_payload = self._ticker_to_coin_payload(conf[refund_field])

        if do_encode:
            return urlsafe_b64encode(pb_buffer)
        else:
            return pb_buffer

    def process_transaction(self, conf: Dict, fees: bytes) -> RAPDU:
        if self._subcommand == SubCommand.FUND:
            response = NewFundResponse
            req_conf = ["user_id", "account_name", "in_currency", "in_amount", "in_address"]
            do_encode=True
            payout_field="in_currency"
            refund_field= None
        elif self._subcommand == SubCommand.SELL:
            response = NewSellResponse
            req_conf = ["trader_email", "in_currency", "in_amount", "in_address", "out_currency", "out_amount"]
            do_encode=True
            payout_field="in_currency"
            refund_field= None
        else:
            response = NewTransactionResponse
            req_conf = ["payin_address", "payin_extra_id", "refund_address", "refund_extra_id",
                        "payout_address", "payout_extra_id", "currency_from", "currency_to",
                        "amount_to_provider", "amount_to_wallet"]
            do_encode=False
            payout_field="currency_to"
            refund_field= "currency_from"

        self._transaction = self._process_transaction_payload(response, conf, req_conf, do_encode, payout_field, refund_field)
        payload = concatenate(self._transaction, fees)
        return self._exchange(Command.PROCESS_TRANSACTION_RESPONSE, payload=payload)

    def check_transaction(self) -> RAPDU:
        # preparing payload to sign
        payload_to_sign = self._transaction
        # For SELL and FUND subcommand, prefix sign payload by a '.'
        if self._subcommand in [SubCommand.FUND, SubCommand.SELL]:
            payload_to_sign = b"." + payload_to_sign
        signature = self._partner_privkey.sign(payload_to_sign, ec.ECDSA(hashes.SHA256()))
        if self._subcommand == SubCommand.SELL:
            # For SELL subcommand, convert DER encoding to plain r,s
            r, s = decode_dss_signature(signature)
            signature = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        return self._exchange(Command.CHECK_TRANSACTION_SIGNATURE, payload=signature)

    def check_address(self, right_clicks: int, accept: bool = True) -> None:
        if self._subcommand in [SubCommand.SELL, SubCommand.FUND]:
            command = Command.CHECK_PAYOUT_ADDRESS
            payload = self._payout_payload
        elif self._subcommand == SubCommand.SWAP:
            self._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=self._payout_payload)
            command = Command.CHECK_REFUND_ADDRESS
            payload = self._refund_payload
        else:
            raise NotImplementedError()
        with self._exchange_async(command, payload=payload):
            for _ in range(right_clicks):
                self._client.right_click()
            if not accept:
                self._client.right_click()
            self._client.both_click()

    def start_signing_transaction(self) -> RAPDU:
        self._exchange(Command.START_SIGNING_TRANSACTION)
