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
        # Default behaviors
        snapshots_dir_name = self.snapshots_dir_name
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
                                                        path=self._snapshots_path,
                                                        test_case_name=snapshots_dir_name,
                                                        screen_change_after_last_instruction=screen_change_after_last_instruction)

    def simple_accept(self):
        self._navigate_and_compare(True)

    def simple_reject(self):
        self._navigate_and_compare(False)

    def wait_for_exchange_spinner(self):
        if not self._backend.firmware.is_nano:
            self._backend.wait_for_text_on_screen("Processing")

    def wait_for_library_spinner(self):
        if not self._backend.firmware.is_nano:
            self._backend.wait_for_text_on_screen("Signing")

    def check_post_sign_display(self):
        if not self._backend.firmware.is_nano:
            # Wait for the end of the lib app spinner
            self._backend.wait_for_text_not_on_screen("Signing")
            # We should now be back in exchange with a success or failure modal, check it and dismiss it
            self._navigator.navigate_and_compare(path=self._snapshots_path,
                                                 test_case_name=self.snapshots_dir_name + "/post_sign",
                                                 instructions=[NavInsID.USE_CASE_STATUS_DISMISS],
                                                 screen_change_before_first_instruction=False)
