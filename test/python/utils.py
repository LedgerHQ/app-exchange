from pathlib import Path
from time import sleep

def handle_lib_call_start_or_stop(backend):
    # Give some time to actually start the new app
    sleep(1)

    # The USB stack will be reset by the called app
    backend.handle_usb_reset()
