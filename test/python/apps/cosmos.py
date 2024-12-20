import traceback
import requests
import json
from enum import IntEnum

from nacl.encoding import HexEncoder
from nacl.signing import VerifyKey,SigningKey
from nacl.exceptions import BadSignatureError

from ragger.utils import create_currency_config
from ragger.bip import pack_derivation_path, bitcoin_pack_derivation_path, BtcDerivationPathFormat
from ragger.error import ExceptionRAPDU
from scalecodec.base import RuntimeConfiguration
from scalecodec.type_registry import load_type_registry_preset
from scalecodec.utils.ss58 import ss58_decode

from ecdsa import VerifyingKey, SECP256k1
from ecdsa.util import string_to_number

COSMOS_CONF = create_currency_config("ATOM", "Cosmos")
COSMOS_PACKED_DERIVATION_PATH = bitcoin_pack_derivation_path(BtcDerivationPathFormat.LEGACY, "m/44'/118'/5'/0'/3")
COSMOS_PACKED_DERIVATION_PATH_SIGN_INIT = bytes([0x2c, 0x00, 0x00, 0x80,
                                              0x76, 0x00, 0x00, 0x80,
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

class CosmosClient:
    CLA = 0x55
    def __init__(self, client):
        self._client = client

    @property
    def client(self):
        return self._client

    def get_pubkey(self):
        # sizeof(cosmos) + cosmos
        data = bytes([0x06,0x63, 0x6f, 0x73, 0x6d, 0x6f, 0x73]) + COSMOS_PACKED_DERIVATION_PATH_SIGN_INIT
        msg = self.client.exchange(self.CLA, ins=Ins.GET_PUBLIC_KEY, p1=GetAddrP1.NO_CONFIRM, data=data)
        return msg.data[:32].hex().encode()

        
    def perform_cosmos_transaction(self, destination, send_amount, fees, memo) -> bytes:
        # Get public key.
        key = self.get_pubkey()

        #Amounts are in uatom for the app aprser to return ATOM ticker and format
        tx = f'''{{"account_number":"0","chain_id":"cosmoshub-4","fee":{{"amount":[{{"amount":"{fees}","denom":"uatom"}}],"gas":"10000"}},"memo":"{memo}","msgs":[{{"inputs":[{{"address":"{destination}","coins":[{{"amount":"{send_amount}","denom":"uatom"}}]}}],"outputs":[{{"address":"{destination}","coins":[{{"amount":"{send_amount}","denom":"uatom"}}]}}]}}],"sequence":"1"}}'''

        # Convert the JSON to bytes
        tx_blob = tx.encode('utf-8')
        
        # Send the first chunk of the transaction path + cosmos hrp
        chunk_0 = COSMOS_PACKED_DERIVATION_PATH_SIGN_INIT + bytes([0x06,0x63, 0x6f, 0x73, 0x6d, 0x6f, 0x73])
        self.client.exchange(self.CLA, ins=Ins.SIGN, p1=SignP1.INIT, data=chunk_0)

        message_splited = [tx_blob[x:x + MAX_CHUNK_SIZE] for x in range(0, len(tx_blob), MAX_CHUNK_SIZE)]
        for index, chunk in enumerate(message_splited):
            payload_type = SignP1.ADD
            if index == len(message_splited) - 1:
                    payload_type = SignP1.LAST

            response = self.client.exchange(self.CLA, ins=Ins.SIGN, p1=payload_type, p2=SignP2.JSON_MODE, data=chunk)

        #TODO: Verify signature
        return True
