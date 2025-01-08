import struct
import hashlib
from enum import IntEnum
from contextlib import contextmanager
from typing import List, Generator
from typing import Dict, List, Union
from pysui.sui.sui_txn.transaction_builder import ProgrammableTransactionBuilder
from pysui.sui.sui_types.bcs import Intent, TransactionData, BuilderArg, Address, TransactionDataV1, GasData, TransactionExpiration, ObjectReference, Digest, Argument, _DIGEST_LENGTH

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.logger import get_default_logger

class INS(IntEnum):
    GET_VERSION     = 0x00 # Gets the app version in machine readable format (bytes)
    VERIFY_ADDRESS  = 0x01 # Shows the Address on device for a BIP32 path
    GET_PUBKEY      = 0x02 # Gets the Public Key and Address for a BIP32 path
    SIGN_TX         = 0x03 # Sign Transaction
    GET_VERSION_STR = 0xFE # Gets the app version in string
    QUIT_APP        = 0xFF # Quits the app

CLA = 0x00

P1 = 0x00
P2 = 0x00

PUBLIC_KEY_LENGTH = 32
BLOCK_CHUNK_SIZE = 180

class ErrorType:
    NO_APP_RESPONSE = 0x6700
    SDK_EXCEPTION = 0x6801
    SDK_INVALID_PARAMETER = 0x6802
    SDK_EXCEPTION_OVERFLOW = 0x6803
    SDK_EXCEPTION_SECURITY = 0x6804
    SDK_INVALID_CRC = 0x6805
    SDK_INVALID_CHECKSUM = 0x6806
    SDK_INVALID_COUNTER = 0x6807
    SDK_INVALID_STATE = 0x6809
    SDK_TIMEOUT = 0x6810
    SDK_EXCEPTION_PIC = 0x6811
    SDK_EXCEPTION_APP_EXIT = 0x6812
    SDK_EXCEPTION_IO_OVERFLOW = 0x6813
    SDK_EXCEPTION_IO_HEADER = 0x6814
    SDK_EXCEPTION_IO_STATE = 0x6815
    SDK_EXCEPTION_IO_RESET = 0x6816
    SDK_EXCEPTION_CX_PORT = 0x6817
    SDK_EXCEPTION_SYSTEM = 0x6818
    SDK_NOT_ENOUGH_SPACE = 0x6819
    SUI_NOT_SUPPORTED            = 0x6808 # `INS` is disabled  (Blind Signing)
    SUI_NOTHING_RECEIVED         = 0x6982 # No input was received by the app
    SUI_ERROR                    = 0x6D00 # Error has occurred due to bad input or user rejected
    SUI_CLA_OR_INS_NOT_SUPPORTED = 0x6E00 # No command exists for the `CLA` and `INS`
    SUI_BAD_LEN                  = 0x6E01 # Length mismatch in inputs
    SUI_OK                       = 0x9000 # Success, or continue if more input from client is expected

    #SUI_BADINS = 0X6E01,
    SUI_BADP1P2 = 0x6E02,
    SUI_BADLEN = 0x6E03,
    SUI_USERCANCELLED = 0x6E04,
    SUI_UNKNOWN = 0x6D00,
    SUI_PANIC = 0xE000,
    SUI_DEVICELOCKED = 0x5515,


class LedgerToHost:
    RESULT_ACCUMULATING = 0
    RESULT_FINAL = 1
    GET_CHUNK = 2
    PUT_CHUNK = 3

class HostToLedger:
    START = 0
    GET_CHUNK_RESPONSE_SUCCESS = 1
    GET_CHUNK_RESPONSE_FAILURE = 2
    PUT_CHUNK_RESPONSE = 3
    RESULT_ACCUMULATING_RESPONSE = 4

class SuiClient:
    client: BackendInterface

    def __init__(self, client: BackendInterface):
        self._client = client
        self.log = print #get_default_logger().debug

    def sui_address_to_list(addr: str):
        return list(bytes.fromhex(addr[2:]))

    def build_simple_transaction(self, sender_addr: str, destination: bytes, send_amount: int) -> bytes:
        tx = b''
        gas_budget = 1000

        # Intent message
        intent_bsc = Intent.encode(Intent.from_list([1,2,3]))
        tx += intent_bsc

        # Build the transaction
        b = ProgrammableTransactionBuilder()

        amount_bytes = list(send_amount.to_bytes(8, byteorder='little'))
        b.input_pure(BuilderArg("Pure", amount_bytes))

        recepient_addr = list(bytes.fromhex(destination[2:].decode('utf-8')))
        recepient_idx = 1
        b.input_pure(BuilderArg("Pure", recepient_addr))

        b.split_coin(Argument("GasCoin"), [BuilderArg("Pure",amount_bytes)])
        b.transfer_objects(Argument("Input", recepient_idx), Argument("Result", 0))

        tx_kind = b.finish_for_inspect()
        tx_data_v1 = TransactionDataV1(
            TransactionKind =  tx_kind,
            Sender= Address.from_str(sender_addr),
            GasData = GasData(
                Payment= [ObjectReference(
                    ObjectID = Address.from_str("0xFEEE"),
                    SequenceNumber= 6666,
                    ObjectDigest= Digest.from_bytes(bytes(_DIGEST_LENGTH)),
                )],
                Owner= Address.from_str(sender_addr),
                Price= 1,
                Budget=gas_budget,
            ),
            TransactionExpiration= TransactionExpiration("None"),
        )

        tx_data = TransactionData("V1", tx_data_v1)
        tx += TransactionData.encode(tx_data)

        return tx

    def sign_transaction(self, path: bytes, txn: Union[str, bytes, bytearray]) -> Dict[str, bytes]:
        """
        Sign a transaction with the key at a BIP32 path.

        :param path: The path to use when signing the transaction.
        :param txn: The transaction, which can be a hex string, bytes, or bytearray.
        :return: the signature.
        """

        if isinstance(txn, str):
            raw_txn = bytes.fromhex(txn)
        else:
            raw_txn = bytes(txn)

        # Transaction payload: length (uint32le) + raw transaction bytes
        hash_size = struct.pack("<I", len(raw_txn))

        # BIP32 key payload
        bip32_key_payload = path

        # Combine hash size and transaction bytes
        payload_txn = hash_size + raw_txn
        self.log("Payload Txn %s", payload_txn)

        ## Send payloads in blocks
        signature = self.send_with_blocks(CLA, INS.SIGN_TX, P1, P2, [payload_txn, bip32_key_payload])
        return signature

    def send_with_blocks(
        self,
        cla: int,
        ins: int,
        p1: int,
        p2: int,
        payload: Union[bytes, List[bytes]],
        extra_data: Dict[str, bytes] = None,
    ) -> bytes:
        if extra_data is None:
            extra_data = {}

        chunk_size = BLOCK_CHUNK_SIZE
        if not isinstance(payload, list):
            payload = [payload]

        parameter_list = []
        data = {**extra_data}

        for block in payload:
            chunk_list = [block[i:i + chunk_size] for i in range(0, len(block), chunk_size)]
            last_hash = b'\x00' * 32
            self.log("%s", last_hash)

            for chunk in reversed(chunk_list):
                linked_chunk = last_hash + chunk
                self.log("Chunk: %s", chunk)
                self.log("linkedChunk: %s", linked_chunk)
                last_hash = hashlib.sha256(linked_chunk).digest()
                data[last_hash.hex()] = linked_chunk

            parameter_list.append(last_hash)
            last_hash = b'\x00' * 32

        self.log("%s", data)

        return self.handle_blocks_protocol(
            cla, ins, p1, p2, bytes([HostToLedger.START]) + b''.join(parameter_list), data
        )

    def handle_blocks_protocol(
        self,
        cla: int,
        ins: int,
        p1: int,
        p2: int,
        initial_payload: bytes,
        data: Dict[str, bytes],
    ) -> bytes:
        payload = initial_payload
        result = b''

        while True:
            self.log("Sending payload to ledger: %s", payload.hex())
            rv = self._client.exchange(cla, ins, p1, p2, payload).data
            self.log("Received response: %s", rv)
            rv_instruction = rv[0]
            rv_payload = rv[1:]

            if rv_instruction not in [LedgerToHost.RESULT_ACCUMULATING, LedgerToHost.RESULT_FINAL,
                                      LedgerToHost.GET_CHUNK, LedgerToHost.PUT_CHUNK]:
                raise TypeError("Unknown instruction returned from ledger")

            if rv_instruction == LedgerToHost.RESULT_ACCUMULATING or rv_instruction == LedgerToHost.RESULT_FINAL:
                result += rv_payload
                payload = bytes([HostToLedger.RESULT_ACCUMULATING_RESPONSE])
                if rv_instruction == LedgerToHost.RESULT_FINAL:
                    self.log("Received final result")
                    break

            elif rv_instruction == LedgerToHost.GET_CHUNK:
                chunk = data.get(rv_payload.hex())
                self.log("Getting block %s", rv_payload)
                self.log("Found block %s", chunk)
                payload = (bytes([HostToLedger.GET_CHUNK_RESPONSE_SUCCESS]) + chunk
                           if chunk else bytes([HostToLedger.GET_CHUNK_RESPONSE_FAILURE]))

            elif rv_instruction == LedgerToHost.PUT_CHUNK:
                data[hashlib.sha256(rv_payload).hexdigest()] = rv_payload
                payload = bytes([HostToLedger.PUT_CHUNK_RESPONSE])

        return result
    
    #@contextmanager
    #def send_async_sign_message(self,
    #                            derivation_path : bytes,
    #                            message: bytes) -> Generator[None, None, None]:
    #    message_splited_prefixed = self.split_and_prefix_message(derivation_path, message)

    #    # Send all chunks with P2_MORE except for the last chunk
    #    # Send all chunks with P2_EXTEND except for the first chunk
    #    if len(message_splited_prefixed) > 1:
    #        final_p2 = P2_EXTEND
    #        self.send_first_message_batch(message_splited_prefixed[:-1], P1_CONFIRM)
    #    else:
    #        final_p2 = 0

    #    with self._client.exchange_async(CLA,
    #                                     INS.INS_SIGN_MESSAGE,
    #                                     P1_CONFIRM,
    #                                     final_p2,
    #                                     message_splited_prefixed[-1]):
    #        yield

    #def get_public_key(self, derivation_path: bytes) -> bytes:
    #    public_key: RAPDU = self._client.exchange(CLA, INS.INS_GET_PUBKEY,
    #                                              P1_NON_CONFIRM, P2_NONE,
    #                                              derivation_path)
    #    assert len(public_key.data) == PUBLIC_KEY_LENGTH, "'from' public key size incorrect"
    #    return public_key.data


    #def split_and_prefix_message(self, derivation_path : bytes, message: bytes) -> List[bytes]:
    #    assert len(message) <= 65535, "Message to send is too long"
    #    header: bytes = _extend_and_serialize_multiple_derivations_paths([derivation_path])
    #    # Check to see if this data needs to be split up and sent in chunks.
    #    max_size = MAX_CHUNK_SIZE - len(header)
    #    message_splited = [message[x:x + max_size] for x in range(0, len(message), max_size)]
    #    # Add the header to every chunk
    #    return [header + s for s in message_splited]


    #def send_first_message_batch(self, messages: List[bytes], p1: int) -> RAPDU:
    #    self._client.exchange(CLA, INS.INS_SIGN_MESSAGE, p1, P2_MORE, messages[0])
    #    for m in messages[1:]:
    #        self._client.exchange(CLA, INS.INS_SIGN_MESSAGE, p1, P2_MORE | P2_EXTEND, m)


    #@contextmanager
    #def send_async_sign_message(self,
    #                            derivation_path : bytes,
    #                            message: bytes) -> Generator[None, None, None]:
    #    message_splited_prefixed = self.split_and_prefix_message(derivation_path, message)

    #    # Send all chunks with P2_MORE except for the last chunk
    #    # Send all chunks with P2_EXTEND except for the first chunk
    #    if len(message_splited_prefixed) > 1:
    #        final_p2 = P2_EXTEND
    #        self.send_first_message_batch(message_splited_prefixed[:-1], P1_CONFIRM)
    #    else:
    #        final_p2 = 0

    #    with self._client.exchange_async(CLA,
    #                                     INS.INS_SIGN_MESSAGE,
    #                                     P1_CONFIRM,
    #                                     final_p2,
    #                                     message_splited_prefixed[-1]):
    #        yield


    #def get_async_response(self) -> RAPDU:
    #    return self._client.last_async_response
