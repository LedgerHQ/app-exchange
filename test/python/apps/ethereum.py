import requests
import pytest

from ragger.utils import pack_APDU, RAPDU
from ragger.error import ExceptionRAPDU
from typing import Iterable

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from ..common import LEDGER_TEST_PRIVATE_KEY


class Command:
    GET_PUBLIC_KEY = 0x02
    SIGN = 0x04
    GET_APP_CONFIGURATION = 0x06
    SIGN_PERSONAL_MESSAGE = 0x08
    PROVIDE_ERC20_TOKEN_INFORMATION = 0x0A
    SIGN_EIP_712_MESSAGE = 0x0C
    GET_ETH2_PUBLIC_KEY = 0x0E
    SET_ETH2_WITHDRAWAL_INDEX = 0x10
    SET_EXTERNAL_PLUGIN = 0x12
    PROVIDE_NFT_INFORMATION = 0x14
    SET_PLUGIN = 0x16
    PERFORM_PRIVACY_OPERATION = 0x18


class P1:
    NON_CONFIRM = 0x00
    FIRST = 0x00
    CONFIRM = 0x01
    MORE = 0x80


class P2:
    NO_CHAINCODE = 0x00
    CHAINCODE = 0x01


class TxType:
    MIN = 0x00
    EIP2930 = 0x01
    EIP1559 = 0x02
    LEGACY = 0xc0
    MAX =  0x7f
    FORCE_LEGACY = 0xf8

TYPE_SIZE = 1
VERSION_SIZE = 1
PLUGIN_NAME_LENGTH_SIZE = 1
ADDRESS_LENGTH= 20
SELECTOR_SIZE= 4
CHAIN_ID_SIZE= 8
KEY_ID_SIZE= 1
ALGORITHM_ID_SIZE= 1
SIGNATURE_LENGTH_SIZE= 1

class SetPluginType:
    ETH_PLUGIN = 0x1

class SetPluginVersion:
    VERSION_1 = 0x1

class ChainID:
    ETHEREUM_CHAIN_ID = 0x01

class KeyId:
    TEST_PLUGIN_KEY = 0x00
    PROD_PLUGIN_KEY = 0x02

class AlgorithmID:
    ECC_SECG_P256K1__ECDSA_SHA_256 = 0x01


ETH_CONF = bytes([
    0x03, 0x45, 0x54, 0x48, 0x08, 0x45, 0x74, 0x68, 0x65, 0x72, 0x65, 0x75,
    0x6D, 0x05, 0x03, 0x45, 0x54, 0x48, 0x12
])

ETH_CONF_DER_SIGNATURE = bytes([
    0x30, 0x44, 0x02, 0x20, 0x65, 0xD7, 0x93, 0x1A, 0xB3, 0x14, 0x43, 0x62,
    0xD5, 0x7E, 0x3F, 0xDC, 0xC5, 0xDE, 0x92, 0x1F, 0xB6, 0x50, 0x24, 0x73,
    0x7D, 0x91, 0x7F, 0x0A, 0xB1, 0xF8, 0xB1, 0x73, 0xD1, 0xED, 0x3C, 0x2E,
    0x02, 0x20, 0x27, 0x49, 0x35, 0x68, 0xD1, 0x12, 0xDC, 0x53, 0xC7, 0x17,
    0x7F, 0x8E, 0x5F, 0xC9, 0x15, 0xD9, 0x1A, 0x90, 0x37, 0x80, 0xA0, 0x67,
    0xBA, 0xDF, 0x10, 0x90, 0x85, 0xA7, 0x3D, 0x36, 0x03, 0x23
])

# length (5) + 44'/60'/0'/0/0
ETH_PACKED_DERIVATION_PATH = bytes([0x05,
                                    0x80, 0x00, 0x00, 0x2c,
                                    0x80, 0x00, 0x00, 0x3c,
                                    0x80, 0x00, 0x00, 0x00,
                                    0x00, 0x00, 0x00, 0x00,
                                    0x00, 0x00, 0x00, 0x00])

LEDGER_NFT_SELECTOR_PUBLIC_KEY = bytes([
    0x04, 0xf5, 0x70, 0x0c, 0xa1, 0xe8, 0x74, 0x24, 0xc7, 0xc7, 0xd1, 0x19, 0xe7, 0xe3,
    0xc1, 0x89, 0xb1, 0x62, 0x50, 0x94, 0xdb, 0x6e, 0xa0, 0x40, 0x87, 0xc8, 0x30, 0x00,
    0x7d, 0x0b, 0x46, 0x9a, 0x53, 0x11, 0xee, 0x6a, 0x1a, 0xcd, 0x1d, 0xa5, 0xaa, 0xb0,
    0xf5, 0xc6, 0xdf, 0x13, 0x15, 0x8d, 0x28, 0xcc, 0x12, 0xd1, 0xdd, 0xa6, 0xec, 0xe9,
    0x46, 0xb8, 0x9d, 0x5c, 0x05, 0x49, 0x92, 0x59, 0xc4])

ERR_SILENT_MODE_CHECK_FAILED = ExceptionRAPDU(0x6001, "ERR_SILENT_MODE_CHECK_FAILED")


class EthereumClient:
    CLA = 0xE0
    def __init__(self, client, derivation_path=b''):
        self._client = client
        self._derivation_path = derivation_path or ETH_PACKED_DERIVATION_PATH

    @property
    def client(self):
        return self._client

    @property
    def derivation_path(self):
        return self._derivation_path

    def _forge_signature_payload(self, additional_payload: bytes):
        return pack_APDU(self.CLA, Command.SIGN, data=(self.derivation_path + additional_payload))

    def _exchange(self,
                  ins: int,
                  p1: int = P1.NON_CONFIRM,
                  p2: int = P2.NO_CHAINCODE,
                  payload: bytes = b''):
        return self.client.exchange(self.CLA, ins=ins, p1=p1, p2=p2, data=payload)

    def get_public_key(self):
        return self._exchange(Command.GET_PUBLIC_KEY, payload=self.derivation_path)

    def set_plugin(self):
        # payload = SetPluginType.ETH_PLUGIN.to_bytes(TYPE_SIZE, byteorder='big')
        # payload += SetPluginVersion.VERSION_1.to_bytes(VERSION_SIZE, byteorder='big')
        # plugin_name = "ERC721"
        # payload += len(plugin_name).to_bytes(PLUGIN_NAME_LENGTH_SIZE, "big")
        # payload += plugin_name.encode()
        # address = "60F80121C31A0D46B5279700F9DF786054AA5EE5"
        # bytes_address = bytes.fromhex(address)
        # assert len(bytes_address) == ADDRESS_LENGTH
        # payload += bytes_address
        # selector = bytes.fromhex("42842e0e")
        # assert len(selector) == SELECTOR_SIZE
        # payload += selector
        # payload += ChainID.ETHEREUM_CHAIN_ID.to_bytes(CHAIN_ID_SIZE, byteorder='big')
        # key_id = KeyId.TEST_PLUGIN_KEY.to_bytes(KEY_ID_SIZE, byteorder='big')
        # payload += key_id
        # algorithm_id = AlgorithmID.ECC_SECG_P256K1__ECDSA_SHA_256.to_bytes(ALGORITHM_ID_SIZE, byteorder='big') # selector
        # payload += algorithm_id

        # payload_to_sign = payload
        # device_number = int.from_bytes(LEDGER_TEST_PRIVATE_KEY, "big")
        # device_privkey = ec.derive_private_key(private_value=device_number, curve=ec.SECP256K1(), backend=default_backend())
        # signature = device_privkey.sign(payload_to_sign, ec.ECDSA(hashes.SHA256()))
        # print("#############")
        # print(signature)
        # print("#############")

        # signature = bytes.fromhex("304502202e2282d7d3ea714da283010f517af469e1d59654aaee0fc438f017aa557eaea50221008b369679381065bbe01135723a4f9adb229295017d37c4d30138b90a51cf6ab6")
        # print(signature)
        # print("#############")
        # payload += len(signature).to_bytes(SIGNATURE_LENGTH_SIZE, "big")
        # payload += signature
        # return self._exchange(Command.SET_PLUGIN, payload=payload)

        api = "https://nft.api.live.ledger-stg.com/v1"
        protocol = "ethereum"
        chainid = ChainID.ETHEREUM_CHAIN_ID
        contract = "60f80121c31a0d46b5279700f9df786054aa5ee5"
        selector = "42842e0e"

        plugin_selector_url = "%s/%s/%d/contracts/0x%s/plugin-selector/0x%s" % \
                                   (api, protocol, chainid, contract, selector)

        payload = requests.get(url = plugin_selector_url).json()["payload"]
        return self._exchange(Command.SET_PLUGIN, payload=bytes.fromhex(payload))

    def provide_nft_information(self):
        api = "https://nft.api.live.ledger-stg.com/v1"
        protocol = "ethereum"
        chainid = ChainID.ETHEREUM_CHAIN_ID
        contract = "60f80121c31a0d46b5279700f9df786054aa5ee5"
        metadata_url = "%s/%s/%d/contracts/0x%s" % (api, protocol, chainid, contract)
        payload = requests.get(url = metadata_url).json()["payload"]
        return self._exchange(Command.PROVIDE_NFT_INFORMATION, payload=bytes.fromhex(payload))

    def sign(self, extra_payload: bytes = bytes.fromhex('eb')):
        # TODO: finish ETH signature with proper payload
        payload = self.derivation_path + extra_payload
        return self._exchange(Command.SIGN, payload=payload)

    def sign_contract(self, extra_payload: bytes = bytes.fromhex('eb')):
        # TODO: finish ETH signature with proper payload
        tx_type = TxType.FORCE_LEGACY.to_bytes(1, byteorder='big')
        random_data_1 = bytes.fromhex("8a0a852c3ce1ec008301f56794")
        contract = bytes.fromhex("60f80121c31a0d46b5279700f9df786054aa5ee5")
        random_data_2 = bytes.fromhex("80b864")
        selector = bytes.fromhex("42842e0e")
        addr_1 = bytes.fromhex("0000000000000000000000006cbcd73cd8e8a42844662f0a0e76d7f79afd933d")
        addr_2 = bytes.fromhex("000000000000000000000000c2907efcce4011c491bbeda8a0fa63ba7aab596c")
        zeroes = bytes.fromhex("000000000000000000000000000000000000000000000000")
        payload = self.derivation_path + tx_type + random_data_1 + contract + random_data_2 + selector + addr_1 + addr_2 + zeroes
        return self._exchange(Command.SIGN, payload=payload)

    def sign_more(self):
        token_id = bytes.fromhex("0000000000112999")
        # TODO: determine what this field is
        magic = bytes.fromhex("018080")
        payload = token_id + magic
        return self._exchange(Command.SIGN, p1=P1.MORE, payload=payload)
