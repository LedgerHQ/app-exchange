import sys
import base58
from pathlib import Path

from enum import IntEnum

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config
from ragger.error import ExceptionRAPDU

sys.path.append(f"{Path(__file__).parent.resolve()}/tron_proto")
'''
Tron Protobuf
'''
from core import Tron_pb2 as tron
from core import Contract_pb2 as Contract
from google.protobuf.any_pb2 import Any

TRX_CONF = create_currency_config("TRX", "Tron")
TRX_USDT_CONF = create_currency_config("USDT", "Tron", ("USDT", 6))
TRX_USDC_CONF = create_currency_config("USDC", "Tron", ("USDC", 6))
TRX_TUSD_CONF = create_currency_config("TUSD", "Tron", ("TUSD", 18))
TRX_USDD_CONF = create_currency_config("USDD", "Tron", ("USDD", 18))

TRX_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/195'/0'")

MAX_APDU_LEN: int = 255
CLA = 0xE0


class InsType(IntEnum):
    GET_PUBLIC_KEY = 0x02
    SIGN = 0x04
    SIGN_TXN_HASH = 0x05  # Unsafe
    GET_APP_CONFIGURATION = 0x06  # Version and settings
    SIGN_PERSONAL_MESSAGE = 0x08
    GET_ECDH_SECRET = 0x0A


class P1():
    # GET_PUBLIC_KEY P1 values
    CONFIRM = 0x01
    NON_CONFIRM = 0x00
    # SIGN P1 values
    SIGN = 0x10
    FIRST = 0x00
    MORE = 0x80
    LAST = 0x90
    TRC10_NAME = 0xA0


class P2():
    # GET_PUBLIC_KEY P2 values
    NO_CHAINCODE = 0x00
    CHAINCODE = 0x01


class TronErrors(IntEnum):
    SW_DENY = 0x6985
    E_MISSING_SETTING_DATA_ALLOWED = 0x6a8b
    SW_SWAP_CHECKING_FAIL = 0x6a8e


class TronClient:
    def __init__(self, backend: BackendInterface):
        if not isinstance(backend, BackendInterface):
            raise TypeError("backend must be an instance of BackendInterface")
        self._backend = backend
        self.owner_address = None

    def _address_hex(self, address):
        return base58.b58decode_check(address).hex().upper()

    def parse_get_public_key_response(
            self, response: bytes) -> (bytes, str):
        # response = public_key_len (1) ||
        #            public_key (var) ||
        #            address_len (1) ||
        #            address (var)
        offset: int = 0

        public_key_len: int = response[offset]
        offset += 1
        public_key: bytes = response[offset:offset + public_key_len]
        offset += public_key_len
        address_len: int = response[offset]
        offset += 1
        address: str = response[offset:offset + address_len].decode("ascii")
        offset += address_len

        assert len(response) == offset
        assert len(public_key) == 65

        return public_key, address

    def send_get_public_key_non_confirm(self, derivation_path: str) -> RAPDU:
        p1 = P1.NON_CONFIRM
        p2 = P2.NO_CHAINCODE
        payload = pack_derivation_path(derivation_path)
        return self._backend.exchange(CLA, InsType.GET_PUBLIC_KEY, p1, p2,
                                      payload)

    def _packContract(self,
                      contractType,
                      contract,
                      data=None,
                      permission_id=None):
        tx = tron.Transaction()
        tx.raw_data.timestamp = 1575712492061
        tx.raw_data.expiration = 1575712551000
        tx.raw_data.ref_block_hash = bytes.fromhex("95DA42177DB00507")
        tx.raw_data.ref_block_bytes = bytes.fromhex("3DCE")
        if data:
            tx.raw_data.custom_data = data.encode()

        c = tx.raw_data.contract.add()
        c.type = contractType
        param = Any()
        param.Pack(contract, deterministic=True)

        c.parameter.CopyFrom(param)

        if permission_id:
            c.Permission_id = permission_id
        return tx.raw_data.SerializeToString()

    def _craft_trx_send_tx(self, memo: str, owner_address: bytes, to_address: bytes, send_amount: int) -> bytes:
        contract = Contract.TransferContract(owner_address=owner_address,
                                             to_address=to_address,
                                             amount=send_amount)

        return self._packContract(tron.Transaction.Contract.TransferContract,
                                  contract,
                                  memo)

    def _craft_trc20_send_tx(self, memo: str, owner_address: bytes, to_address: bytes, send_amount: int, token: str) -> bytes:
        if token == "USDT":
            contract_address = bytes.fromhex("41a614f803b6fd780986a42c78ec9c7f77e6ded13c")
        elif token == "USDC":
            contract_address = bytes.fromhex("413487b63d30b5b2c87fb7ffa8bcfade38eaac1abe")
        elif token == "TUSD":
            contract_address = bytes.fromhex("41cebde71077b830b958c8da17bcddeeb85d0bcf25")
        elif token == "USDD":
            contract_address = bytes.fromhex("4194f24e992ca04b49c6f2a2753076ef8938ed4daa")
        else:
            assert ValueError("Unsupported token")

        data = bytes.fromhex("a9059cbb")  # transfer
        data += bytes.fromhex("00" * 11)
        data += to_address
        data += send_amount.to_bytes(32, "big")

        contract = Contract.TriggerSmartContract(owner_address=owner_address,
                                                 contract_address=contract_address,
                                                 data=data)

        return self._packContract(tron.Transaction.Contract.TriggerSmartContract,
                                  contract,
                                  memo)

    def send_tx(self,
                path: str,
                memo: str,
                destination: str,
                send_amount: int,
                token: str) -> RAPDU:

        if not self.owner_address:
            rapdu = self.send_get_public_key_non_confirm(path)
            _, address = self.parse_get_public_key_response(rapdu.data)
            self.owner_address = bytes.fromhex(self._address_hex(address))

        to_address = bytes.fromhex(self._address_hex(destination))

        data = pack_derivation_path(path)

        if token == "TRX":
            data += self._craft_trx_send_tx(memo, self.owner_address, to_address, send_amount)
        else:
            data += self._craft_trc20_send_tx(memo, self.owner_address, to_address, send_amount, token)
        assert len(data) < MAX_APDU_LEN

        return self._backend.exchange(CLA, InsType.SIGN, P1.SIGN, 0x00, data)
