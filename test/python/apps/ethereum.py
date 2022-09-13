from ragger.utils import pack_APDU, RAPDU
from ragger.error import ExceptionRAPDU

from ..utils import create_currency_config, pack_derivation_path

ETH_CONF = create_currency_config("ETH", "Ethereum", ("ETH", 18))

ETH_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/60'/0'/0/0")


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

    def sign(self, extra_payload: bytes = bytes.fromhex('eb')):
        # TODO: finish ETH signature with proper payload
        payload = self.derivation_path + extra_payload
        return self._exchange(Command.SIGN, payload=payload)


def eth_amount_to_wei_hex_string(eth_amount: int) -> str:
    hex:str = '{:x}'.format(round(eth_amount * 10**18))
    if (len(hex) % 2 != 0):
        hex = "0" + hex
    return hex
