from enum import IntEnum

from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config, RAPDU
from py_near.transactions import create_transfer_action, Transaction
import ed25519
import base58


ED25519_KEYPAIR = "188d2ce61071d477a2400558c3612ee68957a80aa2e56c29dc4da2dace58e7d8c4f5941e81e071c2fd1dae2e71fd3d859d462484391d9a90bf219211dcbb320f"
PRIVATE_KEY = ed25519.SigningKey(bytes.fromhex(ED25519_KEYPAIR))
PUBLIC_KEY = PRIVATE_KEY.get_verifying_key()

NEAR_CONF = create_currency_config("NEAR", "NEAR")

NEAR_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/397'/0'/0'/1'")
SIGNER_ID = "blablatest.testnet"
NONCE = 96520360000015
BLOCK_HASH = base58.b58decode("C32rfeBkSMT1xnsrArkV9Mu81ww9qK7n6Kw17NhEbVuK")


class Ins():
    SIGN = 0x02


class P1():
    START = 0x00
    MORE = 0x80


class P2():
    UNUSED = 0x57


class NearErrors(IntEnum):
    SW_DENY = 0x6985
    SW_SWAP_CHECKING_FAIL = 0x6A88


class NearClient:
    CLA = 0x80

    def __init__(self, backend):
        self._backend = backend

    def send_simple_sign_tx(self, path: str, destination: str, send_amount: int) -> RAPDU:
        packed_path = pack_derivation_path(path)

        tx = Transaction(
                signer_id="blablatest.testnet",
                public_key=PUBLIC_KEY.to_bytes(),
                nonce=NONCE,
                receiver_id=destination,
                actions=[create_transfer_action(send_amount * 10**24)],
                block_hash=BLOCK_HASH
                )

        serialized_tx = bytes(tx.to_vec(PRIVATE_KEY.to_bytes()))

        return self._backend.exchange(self.CLA, Ins.SIGN, P1.MORE, P2.UNUSED, packed_path[1:] + serialized_tx)
