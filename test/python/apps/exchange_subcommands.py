from base64 import urlsafe_b64encode
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Callable, Iterable
from enum import IntEnum, Enum, auto
from dataclasses import dataclass

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.error import ExceptionRAPDU

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


class SignatureComputation(Enum):
    BINARY_ENCODED_PAYLOAD   = auto()
    # For SELL and FUND subcommand, prefix sign payload by a '.'
    DOT_PREFIXED_BASE_64_URL = auto()


class SignatureEncoding(Enum):
    DER       = auto()
    # For SELL subcommand, convert DER encoding to plain r,s
    PLAIN_R_S = auto()


class PayloadEncoding(Enum):
    BYTES_ARRAY = auto()
    BASE_64_URL = auto()


@dataclass(frozen=True)
class SubCommandSpecs:
    curve: ec.EllipticCurve
    signature_computation: SignatureComputation
    signature_encoding: SignatureEncoding
    payload_encoding: PayloadEncoding
    transaction_type: Callable
    required_fields: Iterable[str]
    payout_field: str
    refund_field: Optional[str]

    def check_conf(self, conf: Dict) -> bool:
        return (all(i in conf for i in self.required_fields) and (len(conf) == len(self.required_fields)))

    def compute_payload(self, transaction: bytes) -> bytes:
        if self.signature_computation == SignatureComputation.DOT_PREFIXED_BASE_64_URL:
            return b"." + transaction
        else:
            return transaction

    def encode_payload(self, raw_transaction: bytes) -> bytes:
        if self.payload_encoding == PayloadEncoding.BASE_64_URL:
            return urlsafe_b64encode(raw_transaction)
        else:
            return raw_transaction

    def encode_signature(self, partner_privkey: ec.EllipticCurvePrivateKey, payload_to_sign: bytes) -> bytes:
        signature = partner_privkey.sign(payload_to_sign, ec.ECDSA(hashes.SHA256()))
        if self.signature_encoding == SignatureEncoding.PLAIN_R_S:
            r, s = decode_dss_signature(signature)
            signature = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        return signature

    def create_transaction(self, conf: Dict, transaction_id: bytes) -> bytes:
        raw_transaction = self.transaction_type(**conf, device_transaction_id=transaction_id).SerializeToString()
        return self.encode_payload(raw_transaction)


SWAP_SPECS: SubCommandSpecs = SubCommandSpecs(
    curve = ec.SECP256K1(),
    signature_computation = SignatureComputation.BINARY_ENCODED_PAYLOAD,
    signature_encoding = SignatureEncoding.DER,
    payload_encoding = PayloadEncoding.BYTES_ARRAY,
    transaction_type = NewTransactionResponse,
    required_fields = ["payin_address", "payin_extra_id", "refund_address", "refund_extra_id",
                      "payout_address", "payout_extra_id", "currency_from", "currency_to",
                      "amount_to_provider", "amount_to_wallet"],
    payout_field= "currency_to",
    refund_field= "currency_from"
)

SELL_SPECS: SubCommandSpecs = SubCommandSpecs(
    curve = ec.SECP256R1(),
    signature_computation = SignatureComputation.DOT_PREFIXED_BASE_64_URL,
    signature_encoding = SignatureEncoding.PLAIN_R_S,
    payload_encoding = PayloadEncoding.BASE_64_URL,
    transaction_type = NewSellResponse,
    required_fields = ["trader_email", "in_currency", "in_amount", "in_address", "out_currency", "out_amount"],
    payout_field="in_currency",
    refund_field= None
)

FUND_SPECS: SubCommandSpecs = SubCommandSpecs(
    curve = ec.SECP256R1(),
    signature_computation = SignatureComputation.DOT_PREFIXED_BASE_64_URL,
    signature_encoding = SignatureEncoding.DER,
    payload_encoding = PayloadEncoding.BASE_64_URL,
    transaction_type = NewFundResponse,
    required_fields = ["user_id", "account_name", "in_currency", "in_amount", "in_address"],
    payout_field="in_currency",
    refund_field= None
)