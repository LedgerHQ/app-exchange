import os

from pathlib import Path
from typing import Tuple
from time import sleep

def handle_lib_call_start_or_stop(backend):
    # Give some time to actually start the new app
    sleep(1)

    # The USB stack will be reset by the called app
    backend.handle_usb_reset()


def int_to_minimally_sized_bytes(n: int) -> bytes:
    return n.to_bytes((n.bit_length() + 7) // 8, 'big') or b'\0' # case n is 0


def prefix_with_len_custom(to_prefix: bytes, prefix_length: int = 1) -> bytes:
    prefix = len(to_prefix).to_bytes(prefix_length, byteorder="big")
    print(prefix.hex())
    b = prefix + to_prefix
    return b

makefile_relative_path = "../../Makefile"

makefile_path = (Path(os.path.dirname(os.path.realpath(__file__))) / Path(makefile_relative_path)).resolve()

def get_version_from_makefile() -> Tuple[int, int, int]:
    '''
    Parse the app Makefile to automatically
    '''
    APPVERSION_M = -1
    APPVERSION_N = -1
    APPVERSION_P = -1
    with open(makefile_path) as myfile:
        for line in myfile:
            if line.startswith("APPVERSION_M"):
                _, var = line.partition("=")[::2]
                APPVERSION_M = int(var.strip())
            if line.startswith("APPVERSION_N"):
                _, var = line.partition("=")[::2]
                APPVERSION_N = int(var.strip())
            if line.startswith("APPVERSION_P"):
                _, var = line.partition("=")[::2]
                APPVERSION_P = int(var.strip())

    return APPVERSION_M, APPVERSION_N, APPVERSION_P
