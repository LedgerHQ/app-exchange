from time import sleep
from pathlib import Path

from ragger.navigator import Navigator, NavInsID
from ragger.backend import BackendInterface


class ExchangeNavigationHelper:
    def __init__(self, backend: BackendInterface, snapshots_path: Path, navigator: Navigator, test_name: str):
        self._backend = backend
        self._navigator = navigator
        self._snapshots_path = snapshots_path
        self._test_name = test_name
        self._test_name_suffix = ""

    @property
    def snapshots_dir_name(self) -> str:
        return self._test_name + self._test_name_suffix

    @property
    def snapshots_path(self) -> Path:
        return self._snapshots_path

    def set_test_name_suffix(self, suffix: str):
        self._test_name_suffix = suffix

    def _navigate_and_compare(self, accept: bool):
        if self._backend.firmware.is_nano:
            navigate_instruction = NavInsID.RIGHT_CLICK
            validation_instructions = [NavInsID.BOTH_CLICK]
            text = "Sign transaction" if accept else "Reject transaction"
            # Don't try to assert the "Processing" spinner on Nano, not enabled yet
            screen_change_after_last_instruction = False
        else:
            navigate_instruction = NavInsID.USE_CASE_REVIEW_TAP
            text = "Hold to sign"
            if accept:
                validation_instructions = [NavInsID.USE_CASE_REVIEW_CONFIRM]
            else:
                validation_instructions = [NavInsID.USE_CASE_REVIEW_REJECT, NavInsID.USE_CASE_CHOICE_CONFIRM, NavInsID.USE_CASE_STATUS_DISMISS]
            # Don't try to assert the "Processing" spinner if not validated
            screen_change_after_last_instruction = not accept

        self._navigator.navigate_until_text_and_compare(navigate_instruction=navigate_instruction,
                                                        validation_instructions=validation_instructions,
                                                        text=text,
                                                        path=self._snapshots_path,
                                                        test_case_name=self.snapshots_dir_name + "/review",
                                                        screen_change_after_last_instruction=screen_change_after_last_instruction)

    def _cross_seed_navigate_and_compare(self, accept: bool):
        if self._backend.firmware.is_nano:
            text = "Sign transaction" if accept else "Reject transaction"
            navigate_instruction = NavInsID.RIGHT_CLICK
            validation_instructions = [NavInsID.BOTH_CLICK]
        else:
            navigate_instruction = NavInsID.USE_CASE_REVIEW_TAP
            if accept:
                text = "Continue anyway"
                validation_instructions = [NavInsID.USE_CASE_CHOICE_CONFIRM]
            else:
                text = "Cancel"
                validation_instructions = [NavInsID.USE_CASE_CHOICE_REJECT]

        # Don't try to assert the first screen of the actual review
        screen_change_after_last_instruction = not accept

        self._navigator.navigate_until_text_and_compare(navigate_instruction=navigate_instruction,
                                                        validation_instructions=validation_instructions,
                                                        text=text,
                                                        path=self._snapshots_path,
                                                        test_case_name=self.snapshots_dir_name + "/cross_seed_review",
                                                        screen_change_after_last_instruction=screen_change_after_last_instruction)

    def simple_accept(self):
        self._navigate_and_compare(True)

    def simple_reject(self):
        self._navigate_and_compare(False)

    def cross_seed_accept(self):
        self._cross_seed_navigate_and_compare(True)

    def cross_seed_reject(self):
        self._cross_seed_navigate_and_compare(False)

    def wait_for_exchange_spinner(self):
        if not self._backend.firmware.is_nano:
            self._backend.wait_for_text_on_screen("Processing")

    def wait_for_library_spinner(self):
        if self._backend.firmware.is_nano:
            # Handle applications that do not yet have the Signing spinner on Nano
            sleep(1)
        else:
            self._backend.wait_for_text_on_screen("Signing")

    def check_post_sign_display(self):
        # Wait for the end of the lib app spinner
        self._backend.wait_for_text_not_on_screen("Signing")
        # We should now be back in exchange with a success or failure modal, check it and dismiss it
        if self._backend.firmware.is_nano:
            validation_instructions = [NavInsID.BOTH_CLICK]
        else:
            validation_instructions = [NavInsID.USE_CASE_STATUS_DISMISS]
        self._navigator.navigate_and_compare(path=self._snapshots_path,
                                             test_case_name=self.snapshots_dir_name + "/post_sign",
                                             instructions=validation_instructions,
                                             screen_change_before_first_instruction=False)
