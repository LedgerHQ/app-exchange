from ragger.utils import pack_APDU


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


# length (5) + 44'/60'/0'/0/0
ETH_PACKED_DERIVATION_PATH = bytes([0x05,
                                    0x80, 0x00, 0x00, 0x2c,
                                    0x80, 0x00, 0x00, 0x3c,
                                    0x80, 0x00, 0x00, 0x00,
                                    0x00, 0x00, 0x00, 0x00,
                                    0x00, 0x00, 0x00, 0x00])


class EthereumClient:
    CLA = 0xE0
    def __init__(self, client):
        self._client = client

    @property
    def client(self):
        return self._client

    def _forge_signature_payload(self, additional_payload: bytes):
        return pack_APDU(self.CLA, Command.SIGN, data=(ETH_PACKED_DERIVATION_PATH + additional_payload))

    def _exchange(self,
                  ins: int,
                  p1: int = P1.NON_CONFIRM,
                  p2: int = P2.NO_CHAINCODE,
                  payload: bytes = b''):
        return self.client.exchange(self.CLA, ins=ins, p1=p1, p2=p2, data=payload)

    def get_public_key(self):
        return self._exchange(Command.GET_PUBLIC_KEY, payload=ETH_PACKED_DERIVATION_PATH)

    def sign(self):
        # TODO: finish ETH signature with proper payload
        payload = ETH_PACKED_DERIVATION_PATH + bytes.fromhex('eb')
        return self._exchange(Command.SIGN, payload=payload)
