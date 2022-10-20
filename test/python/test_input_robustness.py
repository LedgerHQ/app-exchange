from .apps.exchange import ExchangeClient, Rate, SubCommand
from ragger.utils import RAPDU
from ragger.backend import RaisePolicy

from .signing_authority import SigningAuthority, LEDGER_SIGNER

INCORRECT_COMMAND_DATA = 0x6A80

def test_flow_name_too_long(client, firmware):
    name = "PARTNER_NAME_123" # Too long
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name=name)

    ex.init_transaction()
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.set_partner_key(partner.credentials)
    assert rapdu.status == INCORRECT_COMMAND_DATA

def test_flow_name_too_short(client, firmware):
    name = "PA" # Too short
    ex = ExchangeClient(client, Rate.FIXED, SubCommand.SWAP)
    partner = SigningAuthority(curve=ex.partner_curve, name=name)

    ex.init_transaction()
    client.raise_policy = RaisePolicy.RAISE_NOTHING
    rapdu: RAPDU = ex.set_partner_key(partner.credentials)
    assert rapdu.status == INCORRECT_COMMAND_DATA
