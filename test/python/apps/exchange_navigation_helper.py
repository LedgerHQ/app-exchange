from pathlib import Path

from ragger.navigator import Navigator, NavInsID
from ragger.backend import BackendInterface

ROOT_SCREENSHOT_PATH = Path(__file__).parent.parent.resolve()

class ExchangeNavigationHelper:
    def __init__(self, backend: BackendInterface, navigator: Navigator, test_name: str):
        self._backend = backend
        self._navigator = navigator
        self._test_name = test_name

    def _navigate_and_compare(self, accept: bool):
        # Default behaviors
        snapshots_dir_name = self._test_name
        screen_change_after_last_instruction = True

        if self._backend.firmware.is_nano:
            navigate_instruction = NavInsID.RIGHT_CLICK
            validation_instructions = [NavInsID.BOTH_CLICK]
            text = "Accept" if accept else "Reject"
        else:
            navigate_instruction = NavInsID.USE_CASE_REVIEW_TAP
            text = "Hold to sign"
            if accept:
                validation_instructions = [NavInsID.USE_CASE_REVIEW_CONFIRM]
                # In this case we'll have a second navigation later to dismiss the final modal
                snapshots_dir_name += "/review"
                # Don't try to assert the "Processing" spinner on stax
                screen_change_after_last_instruction = False
            else:
                validation_instructions = [NavInsID.USE_CASE_REVIEW_REJECT, NavInsID.USE_CASE_CHOICE_CONFIRM, NavInsID.USE_CASE_STATUS_DISMISS]

        self._navigator.navigate_until_text_and_compare(navigate_instruction=navigate_instruction,
                                                        validation_instructions=validation_instructions,
                                                        text=text,
                                                        path=ROOT_SCREENSHOT_PATH,
                                                        test_case_name=snapshots_dir_name,
                                                        screen_change_after_last_instruction=screen_change_after_last_instruction)

    def simple_accept(self):
        self._navigate_and_compare(True)

    def simple_reject(self):
        self._navigate_and_compare(False)

    def wait_through_spinners(self):
        if self._backend.firmware.device == "stax":
            self._backend.wait_for_text_on_screen("Processing")
            self._backend.wait_for_text_on_screen("Signing")

    def check_post_sign_display(self):
        if self._backend.firmware.device == "stax":
            self._backend.wait_for_text_not_on_screen("Signing")
            self._navigator.navigate_and_compare(path=ROOT_SCREENSHOT_PATH,
                                                 test_case_name=self._test_name + "/post_sign",
                                                 instructions=[NavInsID.USE_CASE_REVIEW_TAP],
                                                 screen_change_before_first_instruction=False)
