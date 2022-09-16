from time import sleep
from .apps.exchange import ExchangeClient, Rate, SubCommand 
from .apps.polkadot import PolkadotClient, ERR_SWAP_CHECK_WRONG_METHOD, ERR_SWAP_CHECK_WRONG_DEST_ADDR, ERR_SWAP_CHECK_WRONG_AMOUNT
from .utils import int_to_bytes
from ragger.backend import RaisePolicy
from ragger.error import ExceptionRAPDU
import pytest

DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK = bytes([0x05, 0x00, 0x00, 0xb0, 0x0b, 0x9f, 0x27, 0xc2, 0xd1, 0xd2, 0x16,
                                                0x01, 0x58, 0x51, 0xdc, 0x3a, 0x69, 0xc8, 0xab, 0x52, 0xb2, 0x86,
                                                0x62, 0xe7, 0xfa, 0x31, 0x7c, 0x07, 0xad, 0x1f, 0x34, 0xa4, 0xdf,
                                                0xcd, 0x62, 0x07, 0x70, 0xf9, 0xdb, 0xdf, 0x02, 0x85, 0x02, 0x00,
                                                0x00, 0x36, 0x24, 0x00, 0x00, 0x0d, 0x00, 0x00, 0x00, 0x91, 0xb1,
                                                0x71, 0xbb, 0x15, 0x8e, 0x2d, 0x38, 0x48, 0xfa, 0x23, 0xa9, 0xf1,
                                                0xc2, 0x51, 0x82, 0xfb, 0x8e, 0x20, 0x31, 0x3b, 0x2c, 0x1e, 0xb4,
                                                0x92, 0x19, 0xda, 0x7a, 0x70, 0xce, 0x90, 0xc3, 0x56, 0x2a, 0xc8,
                                                0xd2, 0x83, 0x7a, 0x08, 0x41, 0x8e, 0x98, 0x0e, 0xbf, 0x4a, 0x37,
                                                0x9f, 0x94, 0xae, 0x03, 0x96, 0x37, 0xc5, 0x08, 0xa3, 0xbc, 0xdd,
                                                0x30, 0x1e, 0x77, 0x88, 0xbd, 0xd3, 0x58])

# Wrong amount : DOT 12.3456712345
DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK_WRONG_AMOUNT = bytes([0x05, 0x00, 0x00, 0xb0, 0x0b, 0x9f, 0x27, 0xc2, 0xd1, 0xd2, 0x16,
                                                             0x01, 0x58, 0x51, 0xdc, 0x3a, 0x69, 0xc8, 0xab, 0x52, 0xb2, 0x86,
                                                             0x62, 0xe7, 0xfa, 0x31, 0x7c, 0x07, 0xad, 0x1f, 0x34, 0xa4, 0xdf,
                                                             0xcd, 0x62, 0x07, 0x99, 0xee, 0x97, 0xbe, 0x1c, 0xd5, 0x03, 0x00,
                                                             0x00, 0x36, 0x24, 0x00, 0x00, 0x0d, 0x00, 0x00, 0x00, 0x91, 0xb1,
                                                             0x71, 0xbb, 0x15, 0x8e, 0x2d, 0x38, 0x48, 0xfa, 0x23, 0xa9, 0xf1,
                                                             0xc2, 0x51, 0x82, 0xfb, 0x8e, 0x20, 0x31, 0x3b, 0x2c, 0x1e, 0xb4,
                                                             0x92, 0x19, 0xda, 0x7a, 0x70, 0xce, 0x90, 0xc3, 0xcf, 0x84, 0xc1,
                                                             0x9b, 0x14, 0x0d, 0xa4, 0xbf, 0x74, 0x66, 0xa5, 0xa0, 0xde, 0x98,
                                                             0x1d, 0xf8, 0xf4, 0xdc, 0xf3, 0xf1, 0x61, 0xf6, 0x25, 0xc2, 0xfe,
                                                             0x6c, 0xfa, 0xfa, 0x27, 0x93, 0x82, 0x1a])

# Wrong payin address : 15yvXMFv8gsgxZWCmaxjFsJJfLU9qhT6qrHMoz7a9ZkTsg9A
DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK_WRONG_DEST_ADDR = bytes([0x05, 0x00, 0x00, 0xdc, 0x5a, 0xda, 0x10, 0xee, 0xdd, 0x89, 0x81, 0x92,
                                                                0x78, 0xb0, 0x92, 0x35, 0x87, 0x80, 0x3d, 0x7d, 0xb2, 0x07, 0xe1, 0xdc,
                                                                0x7e, 0x1c, 0x18, 0x42, 0x4f, 0xa4, 0xad, 0x59, 0xb4, 0x00, 0x19, 0x07,
                                                                0x70, 0xf9, 0xdb, 0xdf, 0x02, 0x45, 0x01, 0x00, 0x00, 0x36, 0x24, 0x00,
                                                                0x00, 0x0d, 0x00, 0x00, 0x00, 0x91, 0xb1, 0x71, 0xbb, 0x15, 0x8e, 0x2d,
                                                                0x38, 0x48, 0xfa, 0x23, 0xa9, 0xf1, 0xc2, 0x51, 0x82, 0xfb, 0x8e, 0x20,
                                                                0x31, 0x3b, 0x2c, 0x1e, 0xb4, 0x92, 0x19, 0xda, 0x7a, 0x70, 0xce, 0x90,
                                                                0xc3, 0xc7, 0xf6, 0x65, 0xf3, 0xf9, 0xb3, 0x41, 0x5d, 0xbb, 0xa3, 0xb3,
                                                                0x46, 0xb4, 0xf9, 0x1e, 0xff, 0x30, 0xab, 0xa4, 0xdc, 0xcd, 0xa2, 0x9b,
                                                                0xfd, 0x7c, 0xc8, 0xfd, 0x6a, 0x23, 0xdd, 0xa6, 0x01])

# Wrong method : Force transfer (0x0502)
DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK_WRONG_METHOD = bytes([0x05, 0x02, 0x00, 0xdc, 0x5a, 0xda, 0x10, 0xee, 0xdd, 0x89, 0x81, 0x92, 0x78,
                                                             0xb0, 0x92, 0x35, 0x87, 0x80, 0x3d, 0x7d, 0xb2, 0x07, 0xe1, 0xdc, 0x7e, 0x1c,
                                                             0x18, 0x42, 0x4f, 0xa4, 0xad, 0x59, 0xb4, 0x00, 0x19, 0x00, 0xb0, 0x0b, 0x9f,
                                                             0x27, 0xc2, 0xd1, 0xd2, 0x16, 0x01, 0x58, 0x51, 0xdc, 0x3a, 0x69, 0xc8, 0xab,
                                                             0x52, 0xb2, 0x86, 0x62, 0xe7, 0xfa, 0x31, 0x7c, 0x07, 0xad, 0x1f, 0x34, 0xa4,
                                                             0xdf, 0xcd, 0x62, 0x07, 0x70, 0xf9, 0xdb, 0xdf, 0x02, 0x55, 0x02, 0x00, 0x00,
                                                             0x36, 0x24, 0x00, 0x00, 0x0d, 0x00, 0x00, 0x00, 0x91, 0xb1, 0x71, 0xbb, 0x15,
                                                             0x8e, 0x2d, 0x38, 0x48, 0xfa, 0x23, 0xa9, 0xf1, 0xc2, 0x51, 0x82, 0xfb, 0x8e,
                                                             0x20, 0x31, 0x3b, 0x2c, 0x1e, 0xb4, 0x92, 0x19, 0xda, 0x7a, 0x70, 0xce, 0x90,
                                                             0xc3, 0x17, 0xc3, 0xe2, 0x31, 0xc5, 0xc6, 0x23, 0xc5, 0x91, 0xca, 0xf1, 0x0d,
                                                             0xf0, 0x1b, 0x76, 0xd0, 0xd0, 0xbb, 0x08, 0xa5, 0x01, 0xfc, 0xd1, 0x23, 0x93,
                                                             0x74, 0xed, 0x61, 0x67, 0x79, 0x8b, 0x50 ])


EXCHANGE_EXCEPTION_RAPDU_INVALID_ADDR = ExceptionRAPDU(0x6A83, b"")

def prepare_exchange(client, firmware, 
                     amount: int = 12345670000, 
                     payin_address : bytes = b"14ypt3a2m9yiq4ZQDcJFrkD99C3ZoUjLCDz1gBpCDwJPqVDY",
                     refund_address : bytes = b"14TwSqXEoCPK7Q7Jnk2RFzbPZXppsxz24bHaQ7fakwio7DFn",
                     payout_addr : bytes = b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
                     curr_from : str = "DOT",
                     curr_to : str = "ETH",
                     amount_to_wallet : int = 10000000000000,
                     addresses_ok : bool = True):
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    ex.init_transaction()
    ex.set_partner_key()
    ex.check_partner_key()

    tx_infos = {
        "payin_address": payin_address,
        "payin_extra_id": b"",
        "refund_address": refund_address,
        "refund_extra_id": b"",
        "payout_address": payout_addr,
        "payout_extra_id": b"",
        "currency_from": curr_from,
        "currency_to": curr_to,
        "amount_to_provider": int_to_bytes(amount),
        "amount_to_wallet": int_to_bytes(amount_to_wallet),
    }
    
    fees = int_to_bytes(100000000)

    ex.process_transaction(tx_infos, fees)
    ex.check_transaction()

    right_clicks = {
        "nanos": 4,
        "nanox": 4,
        "nanosp": 4
    }
    
    if(addresses_ok):
       ex.check_address(right_clicks=right_clicks[firmware.device])
    else:
        try:
            client.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
            ex.check_address(right_clicks=right_clicks[firmware.device])
        except ExceptionRAPDU as rapdu:
            assert rapdu.data == EXCHANGE_EXCEPTION_RAPDU_INVALID_ADDR.data
            assert rapdu.status == EXCHANGE_EXCEPTION_RAPDU_INVALID_ADDR.status, f"Received APDU status {hex(rapdu.status)}, expected {hex(EXCHANGE_EXCEPTION_RAPDU_INVALID_ADDR.status)}"
            return
    
    ex.start_signing_transaction()
    
    sleep(0.1)

testdata = [
    (b"bc1qer57ma0fzhqys2cmydhuj9cprf9eg0nw922a8j", "BTC", 100000000), # 1 BTC = 1e8 satoshis
    (b"tz1Mr8aY9Li8L1Qw3Kz7PrbFawmYAHAEUcJ1", "XTZ", 1000000), # 1 XTZ = 1e6 mutez 
    (b"GCFLQQDXVY7VFEAZH25HFSSXEKCYYQSA7YEI3DMJZAEABPV2KMPLCXQ5", "XLM", 1000000), # 1 XLM = 1e6 stroop
    (b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D", "ETH", 1000000000000000000), # 1 ETH = 1e18 wei
    (b"MJovkMvQ2rXXUj7TGVvnQyVMWghSdqZsmu", "LTC", 100000000), # 1 LTC = 1e8 litoshis
    (b"rNAwni2CP9uAwU2qMka8fgNQA5kWKtu2vT", "XRP", 1000000), # 1 XRP = 1e6 drops
]

@pytest.mark.parametrize("payout_addr,curr_to,amount_to_wallet", testdata, ids=["btc","xtz","xlm","eth","ltc","xrp"])
def test_swap_flow_dot_nominal(client, firmware, payout_addr, curr_to, amount_to_wallet):
    prepare_exchange(client,firmware,
                     payout_addr=payout_addr,curr_to=curr_to,amount_to_wallet=amount_to_wallet)
    dot = PolkadotClient(client)
    # Get public key.
    key = dot.get_pubkey()
    # Init signature process and assert response APDU code is 0x9000 (OK).
    assert dot.sign_init().status == 0x9000
    # Send message to be signed
    sign_response = dot.sign_last(DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK)
    # Assert response APDU code is 0x9000 (OK).
    assert sign_response.status == 0x9000
    # Assert signature is verified properly with key and message
    assert dot.verify_signature(hex_key=key,signature=sign_response.data[1:],message=DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK.hex().encode()) == True

def test_swap_flow_dot_eth_wrong_amount(client, firmware):
    prepare_exchange(client,firmware)
    dot = PolkadotClient(client)
    assert dot.sign_init().status == 0x9000
    try:
        client.raise_policy = RaisePolicy.RAISE_ALL
        dot.sign_last(DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK_WRONG_AMOUNT).status
    except ExceptionRAPDU as rapdu:
        assert rapdu.data ==  ERR_SWAP_CHECK_WRONG_AMOUNT.data, f"Received APDU data {rapdu.data}, expected {ERR_SWAP_CHECK_WRONG_AMOUNT.data}"
        assert rapdu.status == ERR_SWAP_CHECK_WRONG_AMOUNT.status, f"Received APDU status {hex(rapdu.status)}, expected {hex(ERR_SWAP_CHECK_WRONG_AMOUNT.status)}"

def test_swap_flow_dot_eth_wrong_amount_then_ok(client, firmware):
    prepare_exchange(client,firmware)
    dot = PolkadotClient(client)
    assert dot.sign_init().status == 0x9000
    try:
        client.raise_policy = RaisePolicy.RAISE_ALL
        dot.sign_last(DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK_WRONG_AMOUNT).status
    except ExceptionRAPDU as rapdu:
        assert rapdu.data ==  ERR_SWAP_CHECK_WRONG_AMOUNT.data, f"Received APDU data {rapdu.data}, expected {ERR_SWAP_CHECK_WRONG_AMOUNT.data}"
        assert rapdu.status == ERR_SWAP_CHECK_WRONG_AMOUNT.status, f"Received APDU status {hex(rapdu.status)}, expected {hex(ERR_SWAP_CHECK_WRONG_AMOUNT.status)}"
        
    client.raise_policy = RaisePolicy.RAISE_ALL_BUT_0x9000
    # Get public key.
    key = dot.get_pubkey()
    # Init signature process and assert response APDU code is 0x9000 (OK).
    assert dot.sign_init().status == 0x9000
    # Send message to be signed
    sign_response = dot.sign_last(DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK)
    # Assert response APDU code is 0x9000 (OK).
    assert sign_response.status == 0x9000
    # Assert signature is verified properly with key and message
    assert dot.verify_signature(hex_key=key,signature=sign_response.data[1:],message=DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK.hex().encode()) == True

def test_swap_flow_dot_eth_wrong_dest_addr(client, firmware):
    prepare_exchange(client,firmware)
    dot = PolkadotClient(client)    
    assert dot.sign_init().status == 0x9000
    try:
        client.raise_policy = RaisePolicy.RAISE_ALL
        dot.sign_last(DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK_WRONG_DEST_ADDR).status
    except ExceptionRAPDU as rapdu:
        assert rapdu.data ==  ERR_SWAP_CHECK_WRONG_DEST_ADDR.data, f"Received APDU data {rapdu.data}, expected {ERR_SWAP_CHECK_WRONG_DEST_ADDR.data}"
        assert rapdu.status == ERR_SWAP_CHECK_WRONG_DEST_ADDR.status, f"Received APDU status {hex(rapdu.status)}, expected {hex(ERR_SWAP_CHECK_WRONG_DEST_ADDR.status)}"

def test_swap_flow_dot_eth_wrong_tx_method(client, firmware):
    prepare_exchange(client,firmware)
    dot = PolkadotClient(client)    
    assert dot.sign_init().status == 0x9000
    try:
        client.raise_policy = RaisePolicy.RAISE_ALL
        dot.sign_last(DOT_PACKED_TRANSACTION_SIGN_LAST_CHUNK_WRONG_METHOD).status
    except ExceptionRAPDU as rapdu:
        assert rapdu.data == ERR_SWAP_CHECK_WRONG_METHOD.data, f"Received APDU data {rapdu.data}, expected {ERR_SWAP_CHECK_WRONG_METHOD.data}"
        assert rapdu.status == ERR_SWAP_CHECK_WRONG_METHOD.status, f"Received APDU status {hex(rapdu.status)}, expected {hex(ERR_SWAP_CHECK_WRONG_METHOD.status)}"

def test_swap_flow_dot_eth_wrong_refund_addr(client, firmware):
    prepare_exchange(client,
                     firmware,
                     refund_address=b"15yvXMFv8gsgxZWCmaxjFsJJfLU9qhT6qrHMoz7a9ZkTsg9A",
                     addresses_ok=False)
    
def test_swap_flow_eth_dot_payout_addr_ok(client, firmware):
    prepare_exchange(
                    client,
                    firmware,
                    amount=1000000000000000000,
                    payin_address=b"0xea3c696e2227C33A83b6069cc9932bcE117475D6",
                    refund_address=b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
                    curr_from="ETH",
                    curr_to="DOT",
                    payout_addr=b"14TwSqXEoCPK7Q7Jnk2RFzbPZXppsxz24bHaQ7fakwio7DFn",
                    amount_to_wallet=10000000000)
    
def test_swap_flow_eth_dot_wrong_payout_addr(client, firmware):
    prepare_exchange(
                    client,
                    firmware,
                    amount=1000000000000000000,
                    payin_address=b"0xea3c696e2227C33A83b6069cc9932bcE117475D6",
                    refund_address=b"0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D",
                    curr_from="ETH",
                    curr_to="DOT",
                    payout_addr=b"15yvXMFv8gsgxZWCmaxjFsJJfLU9qhT6qrHMoz7a9ZkTsg9A",
                    amount_to_wallet=10000000000,
                    addresses_ok=False)