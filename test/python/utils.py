from pathlib import Path

ROOT_SCREENSHOT_PATH = Path(__file__).parent.resolve()

def concatenate(*args):
    result = b''
    for arg in args:
        result += (bytes([len(arg)]) + arg)
    return result

def int_to_bytes(x : int):
    hexstring = "{0:0x}".format(x)
    if len(hexstring)%2: 
        hexstring = '0' + hexstring
    return bytes.fromhex(hexstring)
