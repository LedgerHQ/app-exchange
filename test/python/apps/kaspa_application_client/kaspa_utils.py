from io import BytesIO
from typing import Literal


UINT64_MAX: int = 2**64-1
UINT32_MAX: int = 2**32-1
UINT16_MAX: int = 2**16-1


def read(buf: BytesIO, size: int) -> bytes:
    b: bytes = buf.read(size)

    if len(b) < size:
        raise ValueError(f"Can't read {size} bytes in buffer!")

    return b


def read_uint(buf: BytesIO,
              bit_len: int,
              byteorder: Literal['big', 'little'] = 'little') -> int:
    size: int = bit_len // 8
    b: bytes = buf.read(size)

    if len(b) < size:
        raise ValueError(f"Can't read u{bit_len} in buffer!")

    return int.from_bytes(b, byteorder)
