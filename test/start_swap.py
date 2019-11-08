import socket
import binascii

def _recvall(s, size):
    data = b''
    while size > 0:
        tmp = s.recv(size)
        if len(tmp) == 0:
            print("[-] apduthread: connection with client closed")
            return None
        data += tmp
        size -= len(tmp)
    return data

def test():
    s = socket.socket()
    s.connect(("127.0.0.1", 9999))
    apdu = binascii.unhexlify('E0020100')
    apdu =len(apdu).to_bytes(4, 'big') + apdu
    s.sendall(apdu)
    s.sendall(apdu)

    # receive the APDU server response
    data = _recvall(s, 4)
    size = int.from_bytes(data, byteorder='big')
    packet = _recvall(s, size + 2)

    print('>', binascii.hexlify(packet))

if __name__ == '__main__':
    test()