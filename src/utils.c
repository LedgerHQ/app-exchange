#include "os.h"
#include "cx.h"
#include <stdbool.h>
#include <stdlib.h>
#include "utils.h"
#include "menu.h"

void sendResponse(uint8_t tx, bool approve) {
    G_io_apdu_buffer[tx++] = approve? 0x90 : 0x69;
    G_io_apdu_buffer[tx++] = approve? 0x00 : 0x85;
    // Send back the response, do not restart the event loop
    io_exchange(CHANNEL_APDU | IO_RETURN_AFTER_TX, tx);
    // Display back the original UX
    ui_idle();
}

unsigned int ui_prepro(const bagl_element_t *element) {
    unsigned int display = 1;
    PRINTF("ui_prepro for element at %x of type %d\n", element, element->component.type);
    if (element->component.userid > 0) {
        display = (ux_step == element->component.userid - 1);
        if (display) {
            if (element->component.userid == 1) {
                UX_CALLBACK_SET_INTERVAL(2000);
            }
            else {
            //    UX_CALLBACK_SET_INTERVAL(MAX(3000, 1000 + bagl_label_roundtrip_duration_ms(element, 7)));
            }
        }
    }
    return display;
}
