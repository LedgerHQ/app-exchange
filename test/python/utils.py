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

def save_screenshot(client, path: str):
    screenshot = client.get_screenshot()
    img = Image.open(BytesIO(screenshot))
    img.save(path)
    
def compare_screenshot_with_timeout(client, path: str, timeout_s = 5):
    step = 0.5
    for _ in range(int(timeout_s / step)):
        screenshot = client.get_screenshot()
        if speculos.client.screenshot_equal(path, BytesIO(screenshot)) :
            return True
        sleep(step)
    return False
