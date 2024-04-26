import sys
from enum import IntEnum
from pathlib import Path
from ragger.utils import create_currency_config
from ragger.bip import BtcDerivationPathFormat, bitcoin_pack_derivation_path
from ragger.backend.interface import BackendInterface, RAPDU
from ragger.backend import RaisePolicy

sys.path.append(f"{Path(__file__).parent.resolve()}/bitcoin_client")
from txmaker import createPsbt
from ledger_bitcoin import Client, WalletPolicy, MultisigWallet, AddressType, PartialSignature, segwit_addr
from ledger_bitcoin import Client, Chain, createClient
from ledger_bitcoin.bip380.descriptors import Descriptor

BTC_CONF = create_currency_config("BTC", "Bitcoin")

BTC_PACKED_DERIVATION_PATH = bitcoin_pack_derivation_path(BtcDerivationPathFormat.BECH32, "m/84'/0'/0'/0/0")
BTC_SEGWIT_PACKED_DERIVATION_PATH = bitcoin_pack_derivation_path(BtcDerivationPathFormat.BECH32, "m/84'/0'/0'/0/10")
BTC_TAPROOT_PACKED_DERIVATION_PATH = bitcoin_pack_derivation_path(BtcDerivationPathFormat.BECH32M, "m/86'/0'/0'/0/6")

CHAIN = Chain.MAIN

class BitcoinErrors(IntEnum):
    SW_SWAP_CHECKING_FAIL = 0x6b00

class BitcoinClient:
    def __init__(self, backend: BackendInterface):
        if not isinstance(backend, BackendInterface):
            raise TypeError("backend must be an instance of BackendInterface")
        self._backend = backend
        self._backend.raise_policy = RaisePolicy.RAISE_CUSTOM
        self._backend.whitelisted_status = [0x9000, 0xE000]
        self.client = createClient(backend, chain=CHAIN, debug=True)

    def send_simple_sign_tx(self, in_wallet: WalletPolicy, fees: int, destination: WalletPolicy, send_amount: int) -> RAPDU:
        in_amounts = [send_amount + fees]
        out_amounts = [send_amount]
        psbt = createPsbt(in_wallet, in_amounts, out_amounts, [False], [destination])
        self.client.sign_psbt(psbt, in_wallet, None)

    def get_address_from_wallet(wallet: WalletPolicy):
        desc = Descriptor.from_str(wallet.get_descriptor(False))
        desc.derive(0)
        spk = desc.script_pubkey
        hrp = "bc" if CHAIN == Chain.MAIN else "tb"
        return segwit_addr.encode(hrp, 0, spk[2:])
