import base64
import struct
import hashlib

from enum import IntEnum
from typing import Dict, List, Optional, Union
from pysui_tx.bcs import Intent, TransactionData, Address, TransactionDataV1, GasData, TransactionExpiration, ObjectReference, Digest
from pysui_tx.bcs import ProgrammableTransaction, CallArg, Command, SplitCoin, TransferObjects, TransactionKind, Argument, _DIGEST_LENGTH, ObjectArg
from apps.sui_utils import USDC_OBJECTS_BY_AMOUNT

from ragger.backend.interface import BackendInterface
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
    SUI_BAD_P1P2 = 0x6E02,
    SUI_BAD_LEN = 0x6E03,
    SUI_USER_CANCELLED = 0x6E04,
    SUI_SWAP_TX_PARAM_MISMATCH = 0x6E05,
    SUI_UNKNOWN = 0x6D00,
    SUI_PANIC = 0xE000,
    SUI_DEVICE_LOCKED = 0x5515,

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

    def __init__(self, client: BackendInterface, verbose: bool):
        self._client = client

        if verbose:
            self.log = get_default_logger().debug
        else:
            self.log = lambda *_args, **_kwargs: None

    def build_simple_transaction(self, sender_addr: str, destination: str, send_amount: int, fees: int) -> bytes:
        tx = b''
        gas_budget = fees

        # Intent message,
        # only valid version = 0, scope = 0, app_id = 0 for TransactionData
        intent_bsc = Intent.encode(Intent.from_list([0,0,0]))
        tx += intent_bsc

        amount_bytes = list(send_amount.to_bytes(8, byteorder='little'))
        recepient_addr = list(bytes.fromhex(destination[2:]))
        recepient_idx = 1

        tx_data_v1 = TransactionDataV1(
            TransactionKind = TransactionKind(
                "ProgrammableTransaction", ProgrammableTransaction(
                    Inputs = [
                        CallArg("Pure", amount_bytes),
                        CallArg("Pure", recepient_addr),
                    ],
                    Command = [
                        Command(
                            "SplitCoin", SplitCoin(
                                FromCoin = Argument("GasCoin"),
                                Amount = [Argument("Input", 0)],
                            ),
                        ),
                        Command(
                            "TransferObjects", TransferObjects(
                                Objects = [Argument("Result", 0)],
                                Address = Argument("Input", recepient_idx),
                            ),
                        ),
                    ],
                ),
            ),
            Sender = Address.from_str(sender_addr),
            GasData = GasData(
                Payment = [ObjectReference(
                    ObjectID = Address.from_str("0xFEEE"),
                    SequenceNumber = 6666,
                    ObjectDigest = Digest.from_bytes(bytes(_DIGEST_LENGTH)),
                )],
                Owner = Address.from_str(sender_addr),
                Price = 1,
                Budget = gas_budget,
            ),
            TransactionExpiration = TransactionExpiration("None"),
        )

        tx_data = TransactionData("V1", tx_data_v1)
        tx += TransactionData.encode(tx_data)

        return tx
    
    # Builds a simple transaction for USDC on Sui and returns the raw transaction bytes + object list
    def build_simple_transaction_with_object_list(self, sender_addr: str, destination: str, send_amount: int, fees: int) -> [bytes, [bytes]]:
        tx = b''
        gas_budget = fees

        # Intent message,
        # only valid version = 0, scope = 0, app_id = 0 for TransactionData
        intent_bsc = Intent.encode(Intent.from_list([0,0,0]))
        tx += intent_bsc

        amount_bytes = list(send_amount.to_bytes(8, byteorder='little'))
        recepient_addr = list(bytes.fromhex(destination[2:]))

        # Referenced in tx inputs coin object
        obj_info = USDC_OBJECTS_BY_AMOUNT[send_amount]
        object_list = [
            base64.b64decode(obj_info['obj'])
        ]

        tx_data_v1 = TransactionDataV1(
            TransactionKind = TransactionKind(
                "ProgrammableTransaction", ProgrammableTransaction(
                    Inputs = [
                        CallArg("Object", ObjectArg(
                            "ImmOrOwnedObject",  ObjectReference(
                                ObjectID = Address.from_str(obj_info['object_id']),
                                SequenceNumber = obj_info['version'],
                                ObjectDigest = Digest.from_str(obj_info['digest']),
                            )
                        )),
                        CallArg("Pure", amount_bytes),
                        CallArg("Pure", recepient_addr),
                    ],
                    Command = [
                        Command(
                            "SplitCoin", SplitCoin(
                                FromCoin = Argument("Input", 0),
                                Amount = [Argument("Input", 1)],
                            ),
                        ),
                        Command(
                            "TransferObjects", TransferObjects(
                                Objects = [Argument("Result", 0)],
                                Address = Argument("Input", 2),
                            ),
                        ),
                    ],
                ),
            ),
            Sender = Address.from_str(sender_addr),
            GasData = GasData(
                Payment = [ObjectReference(
                    ObjectID = Address.from_str("0xFEEE"),
                    SequenceNumber = 6666,
                    ObjectDigest = Digest.from_bytes(bytes(_DIGEST_LENGTH)),
                )],
                Owner = Address.from_str(sender_addr),
                Price = 1,
                Budget = gas_budget,
            ),
            TransactionExpiration = TransactionExpiration("None"),
        )

        tx_data = TransactionData("V1", tx_data_v1)
        tx += TransactionData.encode(tx_data)

        return [tx, object_list]


    def sign_transaction(self, path: bytes, txn: Union[str, bytes, bytearray], object_list: Optional[list[bytes]] = None) -> bytes:
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

        if object_list is None:
            object_list = []

        # Transaction payload: length (uint32le) + raw transaction bytes
        hash_size = struct.pack("<I", len(raw_txn))

        # BIP32 key payload
        bip32_key_payload = path

        # Combine hash size and transaction bytes
        payload_txn = hash_size + raw_txn
        self.log("Payload Txn 0x%s", payload_txn.hex())

        num_items = len(object_list).to_bytes(4, byteorder='little')  # First byte is number of items
        list_data = bytearray(num_items)

        # Add each item with its length prefix
        for item in object_list:
            item_len = len(item).to_bytes(4, byteorder='little')  # Length of each item
            list_data.extend(item_len)
            list_data.extend(item)

        if len(object_list) > 0:
            payload = [payload_txn, bip32_key_payload, bytes(list_data)]
        else:
            payload = [payload_txn, bip32_key_payload]

        ## Send payloads in blocks
        signature = self.send_with_blocks(CLA, INS.SIGN_TX, P1, P2, payload)
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
            self.log("last hash: 0x%s", last_hash.hex())

            for chunk in reversed(chunk_list):
                linked_chunk = last_hash + chunk
                self.log("Chunk: 0x%s", chunk.hex())
                self.log("linkedChunk: 0x%s", linked_chunk.hex())
                last_hash = hashlib.sha256(linked_chunk).digest()
                data[last_hash.hex()] = linked_chunk

            parameter_list.append(last_hash)
            last_hash = b'\x00' * 32

        self.log("data: " + ", ".join(f"{key}: {value.hex()}" for key, value in data.items()))

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
            self.log("Sending payload to ledger: 0x%s", payload.hex())
            rv = self._client.exchange(cla, ins, p1, p2, payload).data
            self.log("Received response: 0x%s", rv.hex())
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
                self.log("Getting block 0x%s", rv_payload.hex())
                self.log("Found block 0x%s", chunk.hex())
                payload = (bytes([HostToLedger.GET_CHUNK_RESPONSE_SUCCESS]) + chunk
                           if chunk else bytes([HostToLedger.GET_CHUNK_RESPONSE_FAILURE]))

            elif rv_instruction == LedgerToHost.PUT_CHUNK:
                data[hashlib.sha256(rv_payload).hexdigest()] = rv_payload
                payload = bytes([HostToLedger.PUT_CHUNK_RESPONSE])

        return result
