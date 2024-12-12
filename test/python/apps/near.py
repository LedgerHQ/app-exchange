from enum import IntEnum

from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config, RAPDU

NEAR_CONF = create_currency_config("NEAR", "NEAR")
NEAR_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/397'/0'/0'/1'")

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

        """
        1234.56 NEAR
        Transaction {
            signer_id: "blablatest.testnet",
            public_key: ed25519:EFr6nRvgKKeteKoEH7hudt8UHYiu94Liq2yMM7x2AU9U,
            nonce: 103595482000005,
            receiver_id: "speculos.testnet",
            block_hash: Cb3vKNiF3MUuVoqfjuEFCgSNPT79pbuVfXXd2RxDXc5E,
            actions: [
                Transfer(
                    TransferAction {
                        deposit: 1234560000000000000000000000,
                    },
                ),
            ],
        }
        """

        tx = bytes.fromhex("12000000626c61626c61746573742e746573746e657400c4f5941e81e071c2fd1dae2e71fd3d859d462484391d9a90bf219211dcbb320f85aae733385e00001000000073706563756c6f732e746573746e6574ac299ac1376e375cd39338d8b29225613ef947424b74a3207c1226863a72583101000000030000001049f203b43f34fd0300000000")

        return self._backend.exchange(self.CLA, Ins.SIGN, P1.MORE, P2.UNUSED, packed_path[1:] + tx)
