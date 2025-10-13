from io import BytesIO
from typing import Union
from hashlib import blake2b

from .kaspa_utils import read, read_uint

def hash_init() -> blake2b:
    return blake2b(digest_size=32, key=bytes("TransactionSigningHash", "ascii"))

class TransactionError(Exception):
    pass

class TransactionInput:
    # pylint: disable=too-many-positional-arguments
    def __init__(self,
                value: int,
                tx_id: str,
                index: int,
                address_type: int,
                address_index: int,
                public_key: bytes):
        self.value: int = value                  # 8 bytes
        self.tx_id: bytes = bytes.fromhex(tx_id) # 32 bytes
        self.address_type: int = address_type    # 1 byte
        self.address_index:int  = address_index  # 4 bytes
        self.index: int = index                  # 1 byte
        self.public_key: bytes = public_key      # 32 bytes, but this is not serialized

    def serialize(self) -> bytes:
        return b"".join([
            self.value.to_bytes(8, byteorder="big"),
            self.tx_id,
            self.address_type.to_bytes(1, byteorder="big"),
            self.address_index.to_bytes(4, byteorder="big"),
            self.index.to_bytes(1, byteorder="big")
        ])

    @classmethod
    def from_bytes(cls, hexa: Union[bytes, BytesIO]):
        buf: BytesIO = BytesIO(hexa) if isinstance(hexa, bytes) else hexa

        value: int = read_uint(buf, 8, 'big')
        tx_id: str = read(buf, 32).decode("hex")
        address_type: int = read_uint(buf, 1, 'big')
        address_index: int = read_uint(buf, 4, 'big')
        index: int = read_uint(buf, 1, 'big')
        public_key: bytes = read(buf, 32)

        return cls(
            value=value,
            tx_id=tx_id,
            address_type=address_type,
            address_index=address_index,
            index=index,
            public_key=public_key
        )

class TransactionOutput:
    def __init__(self,
                 value: int,
                 script_public_key: str):
        self.value = value
        self.script_public_key: bytes = bytes.fromhex(script_public_key)

    def serialize(self) -> bytes:
        return b"".join([
            self.value.to_bytes(8, byteorder="big"),
            self.script_public_key
        ])

    @classmethod
    def from_bytes(cls, hexa: Union[bytes, BytesIO]):
        buf: BytesIO = BytesIO(hexa) if isinstance(hexa, bytes) else hexa

        value: int = read_uint(buf, 8, 'big')
        script_public_key: str = read(buf, 34).decode("hex")

        return cls(value=value, script_public_key=script_public_key)

class Transaction:
    # pylint: disable=too-many-positional-arguments
    def __init__(self,
                 version: int,
                 inputs: list[TransactionInput],
                 outputs: list[TransactionOutput],
                 change_address_type: int = 0,
                 change_address_index: int = 0,
                 account: int = 0x80000000,
                 do_check: bool = True) -> None:
        self.version: int = version
        self.inputs: list[TransactionInput] = inputs
        self.outputs: list[TransactionOutput] = outputs
        self.change_address_type: int = change_address_type
        self.change_address_index: int = change_address_index
        self.account: int = account

        if do_check:
            if not 0 <= self.version <= 1:
                raise TransactionError(f"Bad version: '{self.version}'!")

    def serialize_first_chunk(self) -> bytes:
        return b"".join([
            self.version.to_bytes(2, byteorder="big"),
            len(self.outputs).to_bytes(1, byteorder="big"),
            len(self.inputs).to_bytes(1, byteorder="big"),
            self.change_address_type.to_bytes(1, byteorder="big"),
            self.change_address_index.to_bytes(4, byteorder="big"),
            self.account.to_bytes(4, byteorder="big"),
        ])

    def serialize(self) -> bytes:
        return b"".join([
            self.version.to_bytes(2, byteorder="big"),
            len(self.outputs).to_bytes(1, byteorder="big"),
            len(self.inputs).to_bytes(1, byteorder="big")
        ]).join([
            x.serialize() for x in self.inputs
        ]).join([
            x.serialize() for x in self.outputs
        ])

    def get_sighash(self, input_index: int):
        return Sighash(self, input_index).to_hash()

    @classmethod
    def from_bytes(cls, hexa: Union[bytes, BytesIO]):
        buf: BytesIO = BytesIO(hexa) if isinstance(hexa, bytes) else hexa

        version: int = read_uint(buf, 16, byteorder="big")
        tx_output_len: int = read_uint(buf, 8, byteorder="big")
        tx_input_len: int = read_uint(buf, 8, byteorder="big")

        outputs = []
        inputs = []

        for _ in range(tx_output_len):
            outputs.append(TransactionOutput.from_bytes(buf))

        for _ in range(tx_input_len):
            inputs.append(TransactionInput.from_bytes(buf))

        return cls(version=version, inputs=inputs, outputs=outputs)

class Sighash:
    def __init__(self, tx: Transaction, index: int):
        self.tx: Transaction = tx
        self.index = index

    def _calc_prev_outputs_hash(self) -> bytes:
        inner_hash = hash_init()

        for txin in self.tx.inputs:
            inner_hash.update(txin.tx_id)
            inner_hash.update(txin.index.to_bytes(4, "little"))

        return inner_hash.digest()

    def _calc_sequences_hash(self) -> bytes:
        inner_hash = hash_init()

        for _ in self.tx.inputs:
            inner_hash.update((0).to_bytes(8, "little"))

        return inner_hash.digest()

    def _calc_sig_op_count_hash(self) -> bytes:
        inner_hash = hash_init()

        for _ in self.tx.inputs:
            inner_hash.update((1).to_bytes(1, "little"))

        return inner_hash.digest()

    def calc_txin_script_public_key(self, public_key: bytes) -> bytes:
        return b"".join([
            (0x20).to_bytes(1, "little"),
            public_key,
            (0xac).to_bytes(1, "little")
        ])

    def _calc_outputs_hash(self) -> bytes:
        inner_hash = hash_init()

        for txout in self.tx.outputs:
            inner_hash.update(txout.value.to_bytes(8, "little"))
            inner_hash.update((0).to_bytes(2, "little")) # assume script version 0
            if txout.script_public_key[0] == 0xaa:
                inner_hash.update((35).to_bytes(8, "little"))
            else:
                inner_hash.update((txout.script_public_key[0] + 2).to_bytes(8, "little"))

            inner_hash.update(txout.script_public_key)

        return inner_hash.digest()

    def to_hash(self):
        outer_hash = hash_init()
        outer_hash.update(self.tx.version.to_bytes(2, "little"))

        outer_hash.update(self._calc_prev_outputs_hash())
        outer_hash.update(self._calc_sequences_hash())
        outer_hash.update(self._calc_sig_op_count_hash())

        txin = self.tx.inputs[self.index]

        outer_hash.update(txin.tx_id)
        outer_hash.update(txin.index.to_bytes(4, "little"))
        outer_hash.update((0).to_bytes(2, "little")) # assume input script version 0

        outer_hash.update((34).to_bytes(8, "little"))
        outer_hash.update(self.calc_txin_script_public_key(txin.public_key))

        outer_hash.update(txin.value.to_bytes(8, "little"))
        outer_hash.update((0).to_bytes(8, "little")) # sequence, assume 0
        outer_hash.update((1).to_bytes(1, "little")) # sigopcount, assume 1

        outer_hash.update(self._calc_outputs_hash())

        # Last bits of data, assumed 0 for all
        outer_hash.update((0).to_bytes(8, "little"))  # locktime
        outer_hash.update((0).to_bytes(20, "little")) # subnetwork id
        outer_hash.update((0).to_bytes(8, "little"))  # gas
        outer_hash.update((0).to_bytes(32, "little")) # payload hash

        outer_hash.update((1).to_bytes(1, "little"))  # sighash type

        return outer_hash.digest()
