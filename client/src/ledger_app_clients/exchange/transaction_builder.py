from base64 import urlsafe_b64encode
from typing import Optional, Dict, Callable, Iterable, Union
from enum import Enum, auto, IntEnum
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from ragger.utils import prefix_with_len

from .pb.exchange_pb2 import NewFundResponse, NewSellResponse, NewTransactionResponse
from .signing_authority import SigningAuthority
from .utils import int_to_minimally_sized_bytes, prefix_with_len_custom

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


class SubCommand(IntEnum):
    SWAP = 0x00
    SELL = 0x01
    FUND = 0x02
    SWAP_NG = 0x03
    SELL_NG = 0x04
    FUND_NG = 0x05

    @property
    def get_operation(self):
        return self.name.split('_')[0].lower()

SWAP_SUBCOMMANDS = [SubCommand.SWAP, SubCommand.SWAP_NG]
SELL_SUBCOMMANDS = [SubCommand.SELL, SubCommand.SELL_NG]
FUND_SUBCOMMANDS = [SubCommand.FUND, SubCommand.FUND_NG]
LEGACY_SUBCOMMANDS = [SubCommand.SWAP, SubCommand.SELL, SubCommand.FUND]
NEW_SUBCOMMANDS = [SubCommand.SWAP_NG, SubCommand.SELL_NG, SubCommand.FUND_NG]
ALL_SUBCOMMANDS = [SubCommand.SWAP, SubCommand.SELL, SubCommand.FUND, SubCommand.SWAP_NG, SubCommand.SELL_NG, SubCommand.FUND_NG]

@dataclass()
class SubCommandSpecs:
    subcommand_id: SubCommand
    partner_curve: ec.EllipticCurve
    signature_computation: SignatureComputation
    signature_encoding: SignatureEncoding
    payload_encoding: PayloadEncoding
    transaction_type: Callable
    possible_fields: Iterable[str]
    transaction_id_field: str

    @property
    def dot_prefix(self):
        return int.to_bytes(1 if (self.signature_computation == SignatureComputation.DOT_PREFIXED_BASE_64_URL) else 0, 1, byteorder='big')
    @property
    def signature_encoding_prefix(self):
        return int.to_bytes(1 if (self.signature_encoding == SignatureEncoding.PLAIN_R_S) else 0, 1, byteorder='big')
    @property
    def payload_encoding_prefix(self):
        return int.to_bytes(1 if (self.payload_encoding == PayloadEncoding.BASE_64_URL) else 0, 1, byteorder='big')
    @property
    def is_ng(self):
        return (self.subcommand_id == SubCommand.SWAP_NG or self.subcommand_id == SubCommand.SELL_NG or self.subcommand_id == SubCommand.FUND_NG)
    @property
    def size_of_transaction_length(self):
        return (2 if self.is_ng else 1)

    def check_conf(self, conf: Dict) -> bool:
        # No unknown memmbers in the Dict
        # We accept crafting pb with missing fields
        return all(key in self.possible_fields for key in conf)

    def format_transaction(self, transaction: bytes) -> bytes:
        if self.signature_computation == SignatureComputation.DOT_PREFIXED_BASE_64_URL:
            return b"." + transaction
        else:
            return transaction

    def encode_payload(self, raw_transaction: bytes) -> bytes:
        if self.payload_encoding == PayloadEncoding.BASE_64_URL:
            return urlsafe_b64encode(raw_transaction)
        else:
            return raw_transaction

    def encode_signature(self, signature_to_encode: bytes) -> bytes:
        if self.signature_encoding == SignatureEncoding.PLAIN_R_S:
            r, s = decode_dss_signature(signature_to_encode)
            signature_to_encode = r.to_bytes(32, "big") + s.to_bytes(32, "big")

        if self.is_ng:
            signature_to_encode = self.dot_prefix + self.signature_encoding_prefix + signature_to_encode

        return signature_to_encode

    def create_transaction(self, conf: Dict, transaction_id: bytes) -> bytes:
        # Alter a copy of conf to not modify the actual conf
        c = conf.copy()
        c[self.transaction_id_field] = transaction_id
        print(self.transaction_type(**c))
        raw_transaction = self.transaction_type(**c).SerializeToString()
        return self.encode_payload(raw_transaction)

    def craft_pb(self, tx_infos: Dict, transaction_id: bytes) -> bytes:
        assert self.check_conf(tx_infos)
        return self.create_transaction(tx_infos, transaction_id)

    def craft_transaction(self, transaction: bytes, fees: int) -> bytes:
        fees_bytes = int_to_minimally_sized_bytes(fees)
        payload = prefix_with_len_custom(transaction, self.size_of_transaction_length) + prefix_with_len(fees_bytes)
        if self.is_ng:
            payload = self.payload_encoding_prefix + payload
        return payload

    def encode_transaction_signature(self, signer: SigningAuthority, tx: bytes) -> bytes:
        formated_transaction = self.format_transaction(tx)
        signed_transaction = signer.sign(formated_transaction)
        encoded_signature = self.encode_signature(signed_transaction)
        return encoded_signature

SWAP_NG_SPECS = SubCommandSpecs(
    subcommand_id = SubCommand.SWAP_NG,
    partner_curve = ec.SECP256R1(),
    signature_computation = SignatureComputation.DOT_PREFIXED_BASE_64_URL,
    signature_encoding = SignatureEncoding.PLAIN_R_S,
    payload_encoding = PayloadEncoding.BASE_64_URL,
    transaction_type = NewTransactionResponse,
    possible_fields = ["payin_address", "payin_extra_id", "payin_extra_data", "refund_address", "refund_extra_id",
                       "payout_address", "payout_extra_id", "currency_from", "currency_to",
                       "amount_to_provider", "amount_to_wallet"],
    transaction_id_field = "device_transaction_id_ng",
)

SWAP_SPECS = SubCommandSpecs(
    subcommand_id = SubCommand.SWAP,
    partner_curve = ec.SECP256K1(),
    signature_computation = SignatureComputation.BINARY_ENCODED_PAYLOAD,
    signature_encoding = SignatureEncoding.DER,
    payload_encoding = PayloadEncoding.BYTES_ARRAY,
    transaction_type = NewTransactionResponse,
    possible_fields = ["payin_address", "payin_extra_id", "payin_extra_data", "refund_address", "refund_extra_id",
                       "payout_address", "payout_extra_id", "currency_from", "currency_to",
                       "amount_to_provider", "amount_to_wallet"],
    transaction_id_field = "device_transaction_id",
)

SELL_NG_SPECS = SubCommandSpecs(
    subcommand_id = SubCommand.SELL_NG,
    partner_curve = ec.SECP256R1(),
    signature_computation = SignatureComputation.DOT_PREFIXED_BASE_64_URL,
    signature_encoding = SignatureEncoding.PLAIN_R_S,
    payload_encoding = PayloadEncoding.BASE_64_URL,
    transaction_type = NewSellResponse,
    transaction_id_field = "device_transaction_id",
    possible_fields = ["trader_email", "in_currency", "in_amount", "in_address", "in_extra_id", "out_currency", "out_amount"],
)

SELL_SPECS = SubCommandSpecs(
    subcommand_id = SubCommand.SELL,
    partner_curve = ec.SECP256R1(),
    signature_computation = SignatureComputation.DOT_PREFIXED_BASE_64_URL,
    signature_encoding = SignatureEncoding.PLAIN_R_S,
    payload_encoding = PayloadEncoding.BASE_64_URL,
    transaction_type = NewSellResponse,
    transaction_id_field = "device_transaction_id",
    possible_fields = ["trader_email", "in_currency", "in_amount", "in_address", "in_extra_id", "out_currency", "out_amount"],
)

FUND_NG_SPECS = SubCommandSpecs(
    subcommand_id = SubCommand.FUND_NG,
    partner_curve = ec.SECP256R1(),
    signature_computation = SignatureComputation.DOT_PREFIXED_BASE_64_URL,
    signature_encoding = SignatureEncoding.PLAIN_R_S,
    payload_encoding = PayloadEncoding.BASE_64_URL,
    transaction_type = NewFundResponse,
    possible_fields = ["user_id", "account_name", "in_currency", "in_amount", "in_address", "in_extra_id"],
    transaction_id_field = "device_transaction_id",
)

FUND_SPECS = SubCommandSpecs(
    subcommand_id = SubCommand.FUND,
    partner_curve = ec.SECP256R1(),
    signature_computation = SignatureComputation.DOT_PREFIXED_BASE_64_URL,
    signature_encoding = SignatureEncoding.DER,
    payload_encoding = PayloadEncoding.BASE_64_URL,
    transaction_type = NewFundResponse,
    possible_fields = ["user_id", "account_name", "in_currency", "in_amount", "in_address", "in_extra_id"],
    transaction_id_field = "device_transaction_id",
)

SUBCOMMAND_TO_SPECS = {
    SubCommand.SWAP: SWAP_SPECS,
    SubCommand.SELL: SELL_SPECS,
    SubCommand.FUND: FUND_SPECS,
    SubCommand.SWAP_NG: SWAP_NG_SPECS,
    SubCommand.SELL_NG: SELL_NG_SPECS,
    SubCommand.FUND_NG: FUND_NG_SPECS,
}

def craft_and_sign_tx(subcommand: Union[SubCommand, SubCommandSpecs], tx_infos: Dict, transaction_id: bytes, fees: int, signer: SigningAuthority):
    if isinstance(subcommand, SubCommand):
        subcommand_specs = SUBCOMMAND_TO_SPECS[subcommand]
    else:
        subcommand_specs = subcommand
    pb = subcommand_specs.craft_pb(tx_infos, transaction_id)
    tx = subcommand_specs.craft_transaction(pb, fees)
    signed_tx = subcommand_specs.encode_transaction_signature(signer, pb)
    return tx, signed_tx

def get_partner_curve(subcommand: SubCommand) -> ec.EllipticCurve:
    return SUBCOMMAND_TO_SPECS[subcommand].partner_curve

def get_credentials(subcommand: SubCommand, partner: SigningAuthority) -> bytes:
    if subcommand == SubCommand.SWAP_NG or subcommand == SubCommand.SELL_NG or subcommand == SubCommand.FUND_NG:
        return partner.credentials_ng
    else:
        return partner.credentials
