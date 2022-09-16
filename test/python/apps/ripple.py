# 0x03 XRP 0x03 XRP 0x00
XRP_CONF = bytes([
    0x03, 0x58, 0x52, 0x50, 0x03, 0x58, 0x52, 0x50, 0x00
])

XRP_CONF_DER_SIGNATURE = bytes([
    0x30, 0x45, 0x02, 0x21, 0x00, 0x90, 0xEA, 0x97, 0x51, 0xD8, 0xA8,
    0x28, 0x75, 0x4B, 0xA2, 0x32, 0xBD, 0xC1, 0xC2, 0xEF, 0x9F, 0x8C,
    0x05, 0x47, 0x60, 0x8F, 0x3A, 0xE5, 0x21, 0x32, 0xA2, 0xD9, 0xEB,
    0x83, 0x03, 0x07, 0xE3, 0x02, 0x20, 0x79, 0xBE, 0x69, 0x9A, 0x56,
    0xDB, 0x93, 0x0D, 0xA3, 0x04, 0xC8, 0x3D, 0xAB, 0xF8, 0x06, 0x93,
    0x8C, 0x86, 0xD6, 0xC7, 0xE2, 0x43, 0xF0, 0x27, 0xAF, 0xF3, 0x8B,
    0x1C, 0xBC, 0xE, 0xDF, 0xFE
])

# length (5) + "44'/144'/0'/0/0"
XRP_PACKED_DERIVATION_PATH = bytes([0x05,
                                    0x80, 0x00, 0x00, 0x2c,
                                    0x80, 0x00, 0x00, 0x90,
                                    0x80, 0x00, 0x00, 0x00,
                                    0x80, 0x00, 0x00, 0x00,
                                    0x80, 0x00, 0x00, 0x00])