from typing import List, Generator, Dict
from enum import IntEnum
from contextlib import contextmanager
from time import sleep
from nacl.signing import VerifyKey

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config

from .hedera_builder import hedera_transaction


class INS(IntEnum):
    INS_GET_APP_CONFIGURATION   = 0x01
    INS_GET_PUBLIC_KEY          = 0x02
    INS_SIGN_TRANSACTION        = 0x04

CLA = 0xE0

P1_CONFIRM = 0x00
P1_NON_CONFIRM = 0x01

P2_EXTEND = 0x01
P2_MORE = 0x02


PUBLIC_KEY_LENGTH = 32

MAX_CHUNK_SIZE = 255


STATUS_OK = 0x9000

HEDERA_CONF = create_currency_config("HBAR", "Hedera")

HEDERA_PACKED_DERIVATION_PATH      = pack_derivation_path("m/44'/3030'/12345'")
HEDERA_PACKED_DERIVATION_PATH_2    = pack_derivation_path("m/44'/3030'/0'/0'")

# Public key for verification
HEDERA_PUBLIC_KEY = "698f0bad5c0c043a5f09cdcbb4c48ddcf6fb2886fa006df26298003fd59dc7c9"

class ErrorType:
    EXCEPTION_USER_REJECTED = 0x6985


def to_zigzag(n):
    return n + n + (n < 0)


class HederaClient:
    client: BackendInterface

    def __init__(self, client: BackendInterface):
        self._client = client

    def get_public_key_non_confirm(self, index: int) -> RAPDU:
        index_b = index.to_bytes(4, "little")
        return self._client.exchange(CLA, INS.INS_GET_PUBLIC_KEY, P1_NON_CONFIRM, 0, index_b)

    @contextmanager
    def get_public_key_confirm(self, index: int) -> Generator[None, None, None]:
        index_b = index.to_bytes(4, "little")
        with self._client.exchange_async(CLA, INS.INS_GET_PUBLIC_KEY, P1_CONFIRM, 0, index_b):
            sleep(0.5)
            yield

    def get_async_response(self) -> RAPDU:
        return self._client.last_async_response

    def get_public_key_raw(self, index: int) -> bytes:
        """
        Get the raw Ed25519 public key for an index.
        
        :param index: The BIP32 path index
        :return: The public key
        """
        response = self.get_public_key_non_confirm(index)
        if len(response.data) >= PUBLIC_KEY_LENGTH:
            return response.data[:PUBLIC_KEY_LENGTH]
        raise ValueError(f"Invalid public key response length")

    def verify_signature(self, public_key: bytes, transaction: bytes, signature: bytes) -> bool:
        """
        Verify the signature of a transaction.
        
        :param public_key: The public key bytes to verify against
        :param transaction: The transaction that was signed (including 4-byte index prefix)
        :param signature: The signature to verify
        :return: True if the signature is valid, False otherwise
        """
        try:
            verify_key = VerifyKey(public_key)
            # The device receives index+transaction but only signs the transaction part
            transaction_without_index = transaction[4:] if len(transaction) > 4 else transaction
            verify_key.verify(transaction_without_index, signature)
            print("Signature verification successful!")
            return True
        except Exception:
            return False

    def sign_transaction(self,
                         index: int,
                         operator_shard_num: int,
                         operator_realm_num: int,
                         operator_account_num: int,
                         transaction_fee: int,
                         memo: str,
                         conf: Dict) -> bytes:
        """
        Sign a transaction with the key at the specified index.
        
        :param index: The index to use when signing the transaction.
        :param operator_shard_num: The shard number of the operator.
        :param operator_realm_num: The realm number of the operator.
        :param operator_account_num: The account number of the operator.
        :param transaction_fee: The transaction fee.
        :param memo: The transaction memo.
        :param conf: The transaction configuration.
        :return: The signature.
        """
        # Build the transaction
        transaction = hedera_transaction(
            operator_shard_num=operator_shard_num,
            operator_realm_num=operator_realm_num,
            operator_account_num=operator_account_num,
            transaction_fee=transaction_fee,
            memo=memo,
            conf=conf
        )
        
        # Prepare the payload with index
        payload = index.to_bytes(4, "little") + transaction
        
        # Send to device for signing
        response = self._client.exchange(CLA, INS.INS_SIGN_TRANSACTION, P1_NON_CONFIRM, 0, payload)
        
        if not response.data or len(response.data) == 0:
            return b''
        
        return response.data

    @contextmanager
    def send_sign_transaction(self,
                              index: int,
                              operator_shard_num: int,
                              operator_realm_num: int,
                              operator_account_num: int,
                              transaction_fee: int,
                              memo: str,
                              conf: Dict) -> Generator[None, None, None]:

        transaction = hedera_transaction(operator_shard_num,
                                         operator_realm_num,
                                         operator_account_num,
                                         transaction_fee,
                                         memo,
                                         conf)

        payload = index.to_bytes(4, "little") + transaction

        with self._client.exchange_async(CLA, INS.INS_SIGN_TRANSACTION, P1_CONFIRM, 0, payload):
            sleep(0.5)
            yield
