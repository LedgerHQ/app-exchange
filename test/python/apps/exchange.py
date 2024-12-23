from contextlib import contextmanager
from typing import Generator, Optional, Dict
from enum import IntEnum

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.firmware import Firmware
from ragger.utils import prefix_with_len

from ..utils import handle_lib_call_start_or_stop, int_to_minimally_sized_bytes, prefix_with_len_custom, get_version_from_makefile
from .exchange_transaction_builder import SubCommand
from .pki.pem_signer import KeySigner

from .pki.tlv import FieldTag, format_tlv

MAX_CHUNK_SIZE = 255

P2_EXTEND = 0x01 << 4
P2_MORE   = 0x02 << 4

KEY_ID_TEST = 0x00
KEY_ID_PROD = 0x07

class Command(IntEnum):
    GET_VERSION                       = 0x02
    START_NEW_TRANSACTION             = 0x03
    SET_PARTNER_KEY                   = 0x04
    CHECK_PARTNER                     = 0x05
    PROCESS_TRANSACTION_RESPONSE      = 0x06
    CHECK_TRANSACTION_SIGNATURE       = 0x07
    GET_CHALLENGE                     = 0x10
    SEND_TRUSTED_NAME_DESCRIPTOR      = 0x11
    CHECK_ASSET_IN_LEGACY_AND_DISPLAY = 0x08
    CHECK_ASSET_IN_AND_DISPLAY        = 0x0B
    CHECK_ASSET_IN_NO_DISPLAY         = 0x0D
    CHECK_PAYOUT_ADDRESS              = 0x08
    CHECK_REFUND_ADDRESS_AND_DISPLAY  = 0x09
    CHECK_REFUND_ADDRESS_NO_DISPLAY   = 0x0C
    PROMPT_UI_DISPLAY                 = 0x0F
    START_SIGNING_TRANSACTION         = 0x0A


class Rate(IntEnum):
    FIXED    = 0x00
    FLOATING = 0x01


class Errors(IntEnum):
    INCORRECT_COMMAND_DATA       = 0x6A80
    DESERIALIZATION_FAILED       = 0x6A81
    WRONG_TRANSACTION_ID         = 0x6A82
    INVALID_ADDRESS              = 0x6A83
    USER_REFUSED                 = 0x6A84
    INTERNAL_ERROR               = 0x6A85
    WRONG_P1                     = 0x6A86
    WRONG_P2_SUBCOMMAND          = 0x6A87
    WRONG_P2_EXTENSION           = 0x6A88
    INVALID_P2_EXTENSION         = 0x6A89
    MEMORY_CORRUPTION            = 0x6A8A
    AMOUNT_FORMATTING_FAILED     = 0x6A8B
    APPLICATION_NOT_INSTALLED    = 0x6A8C
    WRONG_EXTRA_ID_OR_EXTRA_DATA = 0x6A8D
    WRONG_CHALLENGE              = 0x6A8E
    WRONG_TLV_CONTENT            = 0x6A8F
    MISSING_TLV_CONTENT          = 0x6A90
    WRONG_TLV_FORMAT             = 0x6A91
    WRONG_TLV_KEY_ID             = 0x6A92
    WRONG_TLV_SIGNATURE          = 0x6A93
    NO_CERTIFICATE_LOADED        = 0x6A94
    WRONG_CERTIFICATE_DATA       = 0x6A95
    CLASS_NOT_SUPPORTED          = 0x6E00
    MALFORMED_APDU               = 0x6E01
    INVALID_DATA_LENGTH          = 0x6E02
    INVALID_INSTRUCTION          = 0x6D00
    UNEXPECTED_INSTRUCTION       = 0x6D01
    SIGN_VERIFICATION_FAIL       = 0x9D1A
    SUCCESS                      = 0x9000

class PayinExtraDataID(IntEnum):
    NATIVE = 0x00
    EVM_CALLDATA = 0x01
    OP_RETURN = 0x02

EXCHANGE_CLASS = 0xE0


class PKIClient:
    _CLA: int = 0xB0
    _INS: int = 0x06

    def __init__(self, client: BackendInterface) -> None:
        self._client = client

    def send_certificate(self, payload: bytes) -> RAPDU:
        return self._client.exchange(cla=self._CLA,
                                     ins=self._INS,
                                     p1=0x04, # PubKeyUsage = 0x04
                                     p2=0x00,
                                     data=payload)

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
        self._pki_client = PKIClient(self._client)
        self.trusted_name_key_signer = KeySigner("trusted_name.pem")

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

    def _exchange_split(self, ins: int, payload: bytes) -> RAPDU:
        payload_split = [payload[x:x + MAX_CHUNK_SIZE] for x in range(0, len(payload), MAX_CHUNK_SIZE)]
        for i, p in enumerate(payload_split):
            p2 = self.subcommand
            # Send all chunks with P2_MORE except for the last chunk
            if i != len(payload_split) - 1:
                p2 |= P2_MORE
            # Send all chunks with P2_EXTEND except for the first chunk
            if i != 0:
                p2 |= P2_EXTEND
            rapdu = self._client.exchange(self.CLA, ins=ins, p1=self.rate, p2=p2, data=p)

        return rapdu

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
            return self._exchange_split(Command.PROCESS_TRANSACTION_RESPONSE, payload=transaction)

    def check_transaction_signature(self, encoded_transaction: bytes) -> RAPDU:
        return self._exchange(Command.CHECK_TRANSACTION_SIGNATURE, payload=encoded_transaction)

    def get_challenge(self) -> RAPDU:
        return self._exchange(Command.GET_CHALLENGE)

    def send_trusted_name_descriptor(self,
                                     structure_type: Optional[int] = 3,
                                     version: Optional[int] = 2,
                                     trusted_name_type: Optional[int] = 0x06,
                                     trusted_name_source: Optional[int] = 0x06,
                                     trusted_name: Optional[bytes] = b"Whatever",
                                     chain_id: Optional[int] = 0,
                                     address: Optional[bytes] = b"Whatever",
                                     trusted_name_source_contract: Optional[int] = b"",
                                     challenge: Optional[bytes] = bytes.fromhex("01010101"),
                                     signer_key_id: Optional[int] = 0, # test key
                                     signer_algo: Optional[int] = 1, # secp256k1
                                     skip_signature_field: bool = False,
                                     fake_signature_field: bool = False) -> RAPDU:
        payload = b""
        if structure_type is not None:
            payload += format_tlv(FieldTag.TAG_STRUCTURE_TYPE, structure_type)
        if version is not None:
            payload += format_tlv(FieldTag.TAG_VERSION, version)
        if trusted_name_type is not None:
            payload += format_tlv(FieldTag.TAG_TRUSTED_NAME_TYPE, trusted_name_type)
        if trusted_name_source is not None:
            payload += format_tlv(FieldTag.TAG_TRUSTED_NAME_SOURCE, trusted_name_source)
        if trusted_name is not None:
            payload += format_tlv(FieldTag.TAG_TRUSTED_NAME, trusted_name)
        if chain_id is not None:
            payload += format_tlv(FieldTag.TAG_CHAIN_ID, chain_id)
        if address is not None:
            payload += format_tlv(FieldTag.TAG_ADDRESS, address)
        if trusted_name_source_contract is not None:
            payload += format_tlv(FieldTag.TAG_TRUSTED_NAME_SOURCE_CONTRACT, trusted_name_source_contract)
        if challenge is not None:
            payload += format_tlv(FieldTag.TAG_CHALLENGE, challenge)
        if signer_key_id is not None:
            payload += format_tlv(FieldTag.TAG_SIGNER_KEY_ID, signer_key_id)
        if signer_algo is not None:
            payload += format_tlv(FieldTag.TAG_SIGNER_ALGO, signer_algo)
        if not skip_signature_field:
            if fake_signature_field:
                payload += format_tlv(FieldTag.TAG_DER_SIGNATURE,
                                      self.trusted_name_key_signer.sign_data(payload + b"0"))
            else:
                payload += format_tlv(FieldTag.TAG_DER_SIGNATURE,
                                      self.trusted_name_key_signer.sign_data(payload))

        return self._exchange_split(Command.SEND_TRUSTED_NAME_DESCRIPTOR, payload=payload)

    def send_pki_certificate_and_trusted_name_descriptor(self,
                                                         structure_type: Optional[int] = 3,
                                                         version: Optional[int] = 2,
                                                         trusted_name_type: Optional[int] = 0x06,
                                                         trusted_name_source: Optional[int] = 0x06,
                                                         trusted_name: Optional[bytes] = b"Whatever",
                                                         chain_id: Optional[int] = 0,
                                                         address: Optional[bytes] = b"Whatever",
                                                         trusted_name_source_contract: Optional[int] = b"",
                                                         challenge: Optional[bytes] = bytes.fromhex("01010101"),
                                                         signer_key_id: Optional[int] = 0, # test key
                                                         signer_algo: Optional[int] = 1, # secp256k1
                                                         skip_signature_field: bool = False,
                                                         fake_signature_field: bool = False) -> RAPDU:
        # send PKI certificate
        if self._pki_client is None:
            print(f"Ledger-PKI Not supported on '{self._client.firmware.name}'")
        else:
            # pylint: disable=line-too-long
            if self._client.firmware == Firmware.NANOSP:
                cert_apdu = "01010102010211040000000212010013020002140101160400000000200C547275737465645F4E616D6530020004310104320121332102B91FBEC173E3BA4A714E014EBC827B6F899A9FA7F4AC769CDE284317A00F4F6534010135010315473045022100D494B106E217B46BB90BF20A4E9285529C4C8382D9B80FF462F74942579785F802202D68D0F85CD7CA36BDF351FD41332F310E93163BD175F6A92446C14A3329CC8B"  # noqa: E501
            elif self._client.firmware == Firmware.NANOX:
                cert_apdu = "01010102010211040000000212010013020002140101160400000000200C547275737465645F4E616D6530020004310104320121332102B91FBEC173E3BA4A714E014EBC827B6F899A9FA7F4AC769CDE284317A00F4F653401013501021546304402207FCD665B94B43A6E838E8CD68BE52403D38A7E6A98E2CE291AB1C5D24A41101D02207AB1863E5CB127D9E8A680AC63FF2F2CBEA79CE76652A72832EF154BF1AD6477"  # noqa: E501
            elif self._client.firmware == Firmware.STAX:
                cert_apdu = "01010102010211040000000212010013020002140101160400000000200C547275737465645F4E616D6530020004310104320121332102B91FBEC173E3BA4A714E014EBC827B6F899A9FA7F4AC769CDE284317A00F4F65340101350104154730450221008F8FB0117C8D51F0D13A77680C18CA98B4B317C3D6C67F23BF9198410BEDF1A1022023B1052CA43E86E2411831990C64B1E027D85E142AD39F480948E3EF9517E55E"  # noqa: E501
            elif self._client.firmware == Firmware.FLEX:
                cert_apdu = "01010102010211040000000212010013020002140101160400000000200C547275737465645F4E616D6530020004310104320121332102B91FBEC173E3BA4A714E014EBC827B6F899A9FA7F4AC769CDE284317A00F4F6534010135010515473045022100CEF28780DCAFA3A485D83406D519F9AC12FD9B9C3AA7AE798896013F07DD178D022020F01B1AB1D2AAEDA70357F615EAC55E17FE94EC36DF9DE850CEFACBC98D16C8"  # noqa: E501
            # pylint: enable=line-too-long
            self._pki_client.send_certificate(bytes.fromhex(cert_apdu))

        return self.send_trusted_name_descriptor(structure_type=structure_type,
                                                 version=version,
                                                 trusted_name_type=trusted_name_type,
                                                 trusted_name_source=trusted_name_source,
                                                 trusted_name=trusted_name,
                                                 chain_id=chain_id,
                                                 address=address,
                                                 trusted_name_source_contract=trusted_name_source_contract,
                                                 challenge=challenge,
                                                 signer_key_id=signer_key_id,
                                                 signer_algo=signer_algo,
                                                 skip_signature_field=skip_signature_field,
                                                 fake_signature_field=fake_signature_field)

    def check_payout_address(self, payout_configuration: bytes) -> RAPDU:
        return self._exchange(Command.CHECK_PAYOUT_ADDRESS, payload=payout_configuration)

    @contextmanager
    def check_refund_address(self, refund_configuration) -> Generator[None, None, None]:
        with self._exchange_async(Command.CHECK_REFUND_ADDRESS_AND_DISPLAY, payload=refund_configuration) as response:
            yield response

    def check_refund_address_no_display(self, refund_configuration) -> RAPDU:
        return self._exchange(Command.CHECK_REFUND_ADDRESS_NO_DISPLAY, payload=refund_configuration)

    @contextmanager
    def check_asset_in_legacy(self, payout_configuration: bytes) -> Generator[None, None, None]:
        with self._exchange_async(Command.CHECK_ASSET_IN_LEGACY_AND_DISPLAY, payload=payout_configuration) as response:
            yield response

    @contextmanager
    def check_asset_in(self, payout_configuration: bytes) -> Generator[None, None, None]:
        with self._exchange_async(Command.CHECK_ASSET_IN_AND_DISPLAY, payload=payout_configuration) as response:
            yield response

    def check_asset_in_no_display(self, payout_configuration: bytes) -> RAPDU:
        return self._exchange(Command.CHECK_ASSET_IN_NO_DISPLAY, payload=payout_configuration)

    @contextmanager
    def prompt_ui_display(self) -> Generator[None, None, None]:
        with self._exchange_async(Command.PROMPT_UI_DISPLAY) as response:
            yield response

    def start_signing_transaction(self) -> RAPDU:
        rapdu = self._exchange(Command.START_SIGNING_TRANSACTION)

        # The reception of the APDU means that the Exchange app has received the request
        # and will start os_lib_call.
        # We give some time to the OS to actually process the os_lib_call
        if rapdu.status == 0x9000:
            handle_lib_call_start_or_stop(self._client)
        return rapdu

    def assert_exchange_is_started(self):
        # We don't care at all for the subcommand / rate
        version = self.get_version().data
        major, minor, patch = get_version_from_makefile()
        assert version[0] == major
        assert version[1] == minor
        assert version[2] == patch
