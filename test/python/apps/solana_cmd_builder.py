from typing import List
from enum import IntEnum
import base58
from nacl.signing import VerifyKey


PROGRAM_ID_SYSTEM = "11111111111111111111111111111111"
PROGRAM_ID_COMPUTE_BUDGET = "ComputeBudget111111111111111111111111111111"

# Fake blockhash so this example doesn't need a network connection. It should be queried from the cluster in normal use.
FAKE_RECENT_BLOCKHASH = "11111111111111111111111111111111"


def verify_signature(from_public_key: bytes, message: bytes, signature: bytes):
    assert len(signature) == 64, "signature size incorrect"
    verify_key = VerifyKey(from_public_key)
    verify_key.verify(message, signature)


class SystemInstruction(IntEnum):
    CreateAccount           = 0x00
    Assign                  = 0x01
    Transfer                = 0x02
    CreateAccountWithSeed   = 0x03
    AdvanceNonceAccount     = 0x04
    WithdrawNonceAccount    = 0x05
    InitializeNonceAccount  = 0x06
    AuthorizeNonceAccount   = 0x07
    Allocate                = 0x08
    AllocateWithSeed        = 0x09
    AssignWithSeed          = 0x10
    TransferWithSeed        = 0x11
    UpgradeNonceAccount     = 0x12

class ComputeBudgetInstructionType(IntEnum):
    RequestUnits            = 0x00
    RequestHeapFrame        = 0x01
    SetComputeUnitLimit     = 0x02
    SetComputeUnitPrice     = 0x03

class MessageHeader:
    def __init__(self, num_required_signatures: int, num_readonly_signed_accounts: int, num_readonly_unsigned_accounts: int):
        self.num_required_signatures = num_required_signatures
        self.num_readonly_signed_accounts = num_readonly_signed_accounts
        self.num_readonly_unsigned_accounts = num_readonly_unsigned_accounts

    def serialize(self) -> bytes:
        return self.num_required_signatures.to_bytes(1, byteorder='little') + \
               self.num_readonly_signed_accounts.to_bytes(1, byteorder='little') + \
               self.num_readonly_unsigned_accounts.to_bytes(1, byteorder='little')

class AccountMeta:
    pubkey: bytes
    is_signer: bool
    is_writable: bool
    def __init__(self, pubkey: bytes, is_signer: bool, is_writable: bool):
        self.pubkey = pubkey
        self.is_signer = is_signer
        self.is_writable = is_writable

# Only support Transfer instruction for now
# TODO add other instructions if the need arises
class Instruction:
    program_id: bytes
    accounts: List[AccountMeta]
    data: bytes
    from_pubkey: bytes
    to_pubkey: bytes

class SystemInstructionTransfer(Instruction):
    def __init__(self, from_pubkey: bytes, to_pubkey: bytes, amount: int):
        self.from_pubkey = from_pubkey
        self.to_pubkey = to_pubkey
        self.program_id = base58.b58decode(PROGRAM_ID_SYSTEM)
        self.accounts = [AccountMeta(from_pubkey, True, True), AccountMeta(to_pubkey, False, True)]
        self.data = (SystemInstruction.Transfer).to_bytes(4, byteorder='little') + (amount).to_bytes(8, byteorder='little')

class ComputeBudgetInstructionSetComputeUnitLimit(Instruction):
    def __init__(self, units: int):
        self.program_id = base58.b58decode(PROGRAM_ID_COMPUTE_BUDGET)
        self.accounts = []
        self.data = (ComputeBudgetInstructionType.SetComputeUnitLimit).to_bytes(1, byteorder='little') + (units).to_bytes(4, byteorder='little')

class ComputeBudgetInstructionSetComputeUnitPrice(Instruction):
    def __init__(self, microLamports: int):
        self.program_id = base58.b58decode(PROGRAM_ID_COMPUTE_BUDGET)
        self.accounts = []
        self.data = (ComputeBudgetInstructionType.SetComputeUnitPrice).to_bytes(1, byteorder='little') + (microLamports).to_bytes(8, byteorder='little')

# Cheat as we only support 1 SystemInstructionTransfer currently
# TODO add support for multiple transfers and other instructions if the needs arises
class CompiledInstruction:
    program_id_index: int
    accounts: List[int]
    data: bytes

    def __init__(self, program_id_index: int, accounts: List[int], data: bytes):
        self.program_id_index = program_id_index
        self.accounts = accounts
        self.data = data

    def serialize(self) -> bytes:
        serialized: bytes = self.program_id_index.to_bytes(1, byteorder='little')
        serialized += len(self.accounts).to_bytes(1, byteorder='little')
        for account in self.accounts:
            serialized += (account).to_bytes(1, byteorder='little')
        serialized += len(self.data).to_bytes(1, byteorder='little')
        serialized += self.data
        return serialized

# Solana communication message, header + list of public keys used by the instructions + instructions
# with references to the keys array
class Message:
    header: MessageHeader
    account_keys: List[AccountMeta]
    recent_blockhash: bytes
    compiled_instructions: List[CompiledInstruction]

    def __init__(self, instructions: List[Instruction]):
        # Cheat as we only support 1 SystemInstructionTransfer currently and compute budget only
        # TODO add support for multiple transfers and other instructions if the needs arises
        self.account_keys = []
        for instruction in instructions:
            if hasattr(instruction, "from_pubkey") and hasattr(instruction, "to_pubkey"):
                self.account_keys = [instruction.from_pubkey, instruction.to_pubkey] + self.account_keys
            if instruction.program_id not in self.account_keys:
                self.account_keys.append(instruction.program_id)
        self.compiled_instructions = []
        for instruction in instructions:
            accountIndexes = []
            if hasattr(instruction, "from_pubkey") and hasattr(instruction, "to_pubkey"):
                accountIndexes = [self.account_keys.index(instruction.from_pubkey), self.account_keys.index(instruction.to_pubkey)]
            self.compiled_instructions.append(CompiledInstruction(self.account_keys.index(instruction.program_id), accountIndexes, instruction.data))
        self.header = MessageHeader(2, 0, len(self.account_keys) - 2)
        self.recent_blockhash = base58.b58decode(FAKE_RECENT_BLOCKHASH)

    def serialize(self) -> bytes:
        serialized: bytes = self.header.serialize()
        serialized += len(self.account_keys).to_bytes(1, byteorder='little')
        for account_key in self.account_keys:
            serialized += account_key
        serialized += self.recent_blockhash
        serialized += len(self.compiled_instructions).to_bytes(1, byteorder='little')
        for instruction in self.compiled_instructions:
            serialized += instruction.serialize()
        return serialized
