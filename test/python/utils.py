
def concatenate(*args):
    result = b''
    for arg in args:
        result += (bytes([len(arg)]) + arg)
    return result
