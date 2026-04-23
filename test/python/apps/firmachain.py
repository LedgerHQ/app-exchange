import traceback
import requests
import json
from enum import IntEnum

from nacl.encoding import HexEncoder
from nacl.signing import VerifyKey, SigningKey
from nacl.exceptions import BadSignatureError

from ragger.bip import pack_derivation_path
from ragger.error import ExceptionRAPDU

from ecdsa import VerifyingKey, SECP256k1
from ecdsa.util import string_to_number


def get_sub_config(hrp: str) -> bytes:
    cfg = bytearray()
    cfg.append(len(hrp))
    cfg += hrp.encode()
    return cfg

def create_currency_config(main_ticker: str,
                           application_name: str,
                           sub_config: bytes = bytes()) -> bytes:
    cfg = bytearray()
    for elem in [main_ticker.encode(), application_name.encode(), sub_config]:
        cfg.append(len(elem))
        cfg += elem
    return cfg

FIRMACHAIN_CONF = create_currency_config("FCT", "Firmachain", get_sub_config("firma"))
FIRMACHAIN_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/7777777'/5'/0/3")
FIRMACHAIN_PACKED_DERIVATION_PATH_SIGN_INIT = bytes([0x2C, 0x00, 0x00, 0x80,
                                                     0xF1, 0xAD, 0x76, 0x80,
                                                     0x05, 0x00, 0x00, 0x80,
                                                     0x00, 0x00, 0x00, 0x00,
                                                     0x03, 0x00, 0x00, 0x00])
MAX_CHUNK_SIZE = 250

class Errors:
    ERR_SWAP_CHECK_WRONG_METHOD = 0x6984
    ERR_SWAP_CHECK_WRONG_METHOD_ARGS_CNT = 0x6984
    ERR_SWAP_CHECK_WRONG_DEST_ADDR = 0x6984
    ERR_SWAP_CHECK_WRONG_AMOUNT = 0x6984
    ERR_SWAP_CHECK_WRONG_FEES = 0x6984
    ERR_SWAP_CHECK_WRONG_MEMO = 0x6984

class Ins():
    GET_PUBLIC_KEY = 0x04
    SIGN = 0x02

class GetAddrP1:
    NO_CONFIRM = 0x00
    CONFIRM = 0x01

class SignP1:
    INIT = 0x00
    ADD = 0x01
    LAST = 0x02

class SignP2:
    JSON_MODE = 0x00
    TEXTUAL_MODE = 0x01

class FirmachainClient:
    CLA = 0x55
    def __init__(self, client):
        self._client = client

    @property
    def client(self):
        return self._client

    def get_pubkey(self):
        # sizeof(firma) + firma
        data = bytes([0x05, 0x66, 0x69, 0x72, 0x6d, 0x61]) + FIRMACHAIN_PACKED_DERIVATION_PATH_SIGN_INIT
        msg = self.client.exchange(self.CLA, ins=Ins.GET_PUBLIC_KEY, p1=GetAddrP1.NO_CONFIRM, data=data)
        return msg.data[:32].hex().encode()

    def perform_firmachain_transaction(self, destination, send_amount, fees, memo) -> bytes:
        key = self.get_pubkey()

        tx = f'''{{"account_number":"0","chain_id":"colosseum-1","fee":{{"amount":[{{"amount":"{fees}","denom":"ufct"}}],"gas":"10000"}},"memo":"{memo}","msgs":[{{"inputs":[{{"address":"{destination}","coins":[{{"amount":"{send_amount}","denom":"ufct"}}]}}],"outputs":[{{"address":"{destination}","coins":[{{"amount":"{send_amount}","denom":"ufct"}}]}}]}}],"sequence":"1"}}'''

        tx_blob = tx.encode('utf-8')

        chunk_0 = FIRMACHAIN_PACKED_DERIVATION_PATH_SIGN_INIT
        self.client.exchange(self.CLA, ins=Ins.SIGN, p1=SignP1.INIT, data=chunk_0)

        message_splited = [tx_blob[x:x + MAX_CHUNK_SIZE] for x in range(0, len(tx_blob), MAX_CHUNK_SIZE)]
        for index, chunk in enumerate(message_splited):
            payload_type = SignP1.ADD
            if index == len(message_splited) - 1:
                payload_type = SignP1.LAST

            response = self.client.exchange(self.CLA, ins=Ins.SIGN, p1=payload_type, p2=SignP2.JSON_MODE, data=chunk)

        return True
