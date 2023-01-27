from enum import IntEnum, Enum, auto

from ragger.bip import pack_derivation_path
from ragger.utils import create_currency_config, RAPDU

XTZ_CONF = create_currency_config("XTZ", "Tezos")

XTZ_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/1729'/0'")
