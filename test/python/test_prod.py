import pytest

from pathlib import Path
from ragger.navigator import NavInsID, NavIns
from ragger.error import ExceptionRAPDU

from .apps.exchange_navigation_helper import ROOT_SCREENSHOT_PATH
from .apps.exchange import ExchangeClient, Rate, Errors
from .apps.exchange_transaction_builder import get_partner_curve, ALL_SUBCOMMANDS, get_credentials
from .apps.signing_authority import SigningAuthority, LEDGER_SIGNER

# Navigate in the main menu
@pytest.mark.needs_setup('prod_build')
def test_menu(firmware, navigator, test_name):
    if firmware.device.startswith("nano"):
        instructions = [
            NavInsID.RIGHT_CLICK,
            NavInsID.RIGHT_CLICK,
            #NavInsID.RIGHT_CLICK,
        ]
    else:
        instructions = [
            NavInsID.USE_CASE_HOME_SETTINGS,
            NavInsID.USE_CASE_SETTINGS_MULTI_PAGE_EXIT,
        ]
    navigator.navigate_and_compare(ROOT_SCREENSHOT_PATH,
								   test_name,
								   instructions,
                                   screen_change_before_first_instruction=False)


@pytest.mark.needs_setup('prod_build')
@pytest.mark.parametrize("subcommand", ALL_SUBCOMMANDS)
def test_sign_credentials_with_test_public_key(backend, subcommand):
    ex = ExchangeClient(backend, Rate.FIXED, subcommand)
    partner = SigningAuthority(curve=get_partner_curve(subcommand), name="partner")
    partner_fake = SigningAuthority(curve=get_partner_curve(subcommand), name="partner_fake")

    ex.init_transaction()
    credentials = get_credentials(subcommand, partner)
    ex.set_partner_key(credentials)

    with pytest.raises(ExceptionRAPDU) as e:
        ex.check_partner_key(LEDGER_SIGNER.sign(credentials))
    assert e.value.status == Errors.SIGN_VERIFICATION_FAIL
