#include "user_validate_amounts.h"
#include "ux.h"

#define BAGL_FONT_OPEN_SANS_LIGHT_16_22PX_AVG_WIDTH 10
#define BAGL_FONT_OPEN_SANS_REGULAR_10_13PX_AVG_WIDTH 8
#define MAX_CHAR_PER_LINE 25

#define COLOR_BLACK 0x000000
#define COLOR_WHITE 0xFFFFFF
#define COLOR_GRAY 0x999999
#define COLOR_LIGHT_GRAY 0xEEEEEE

#define UI_NANOS_BACKGROUND() {{BAGL_RECTANGLE,0,0,0,128,32,0,0,BAGL_FILL,0,COLOR_WHITE,0,0},NULL,0,0,0,NULL,NULL,NULL}
#define UI_NANOS_ICON_LEFT(userid, glyph) {{BAGL_ICON,userid,3,12,7,7,0,0,0,COLOR_WHITE,0,0,glyph},NULL,0,0,0,NULL,NULL,NULL}
#define UI_NANOS_ICON_RIGHT(userid, glyph) {{BAGL_ICON,userid,117,13,8,6,0,0,0,COLOR_WHITE,0,0,glyph},NULL,0,0,0,NULL,NULL,NULL}
#define UI_NANOS_TEXT(userid, x, y, w, text, font) {{BAGL_LABELINE,userid,x,y,w,12,0,0,0,COLOR_WHITE,0,font|BAGL_FONT_ALIGNMENT_CENTER,0},(char *)text,0,0,0,NULL,NULL,NULL}
// Only one scrolling text per screen can be displayed
#define UI_NANOS_SCROLLING_TEXT(userid, x, y, w, text, font) {{BAGL_LABELINE,userid,x,y,w,12,0x80|10,0,0,COLOR_WHITE,0,font|BAGL_FONT_ALIGNMENT_CENTER,26},(char *)text,0,0,0,NULL,NULL,NULL}

const bagl_element_t* redraw(const bagl_element_t* element) {
    PRINTF("KIKI");
    return element;
}

unsigned int ui_verify_message_signature_nanos_button(unsigned int button_mask, unsigned int button_mask_counter) {
    PRINTF("KUKUKU");
}

int user_validate_amounts(
    char* send_amount,
    char* get_amount,
    char* partner_name) {
    char send[30] = {0};
    int res = snprintf(send, sizeof(send), "Send %s", send_amount);
    if ((res >= sizeof(send)) || (res < 0)) {
        PRINTF("Error: String amount representaition is too big");
        THROW(INVALID_PARAMETER);
    }
    char get[30] = {0};
    res = snprintf(get, sizeof(get), "Get %s", get_amount);
    if ((res >= sizeof(send)) || (res < 0)) {
        PRINTF("Error: String amount representaition is too big");
        THROW(INVALID_PARAMETER);
    }
    bagl_element_t ui_verify_message_signature_nanos[] = {
        UI_NANOS_BACKGROUND(),
        UI_NANOS_ICON_LEFT(0, BAGL_GLYPH_ICON_CROSS),
        UI_NANOS_ICON_RIGHT(0, BAGL_GLYPH_ICON_CHECK),
        UI_NANOS_TEXT(1, 0, 12, 128, send, BAGL_FONT_OPEN_SANS_EXTRABOLD_11px),
        UI_NANOS_TEXT(1, 0, 26, 128, get, BAGL_FONT_OPEN_SANS_EXTRABOLD_11px)
    };
    UX_DISPLAY(ui_verify_message_signature_nanos, redraw);
}