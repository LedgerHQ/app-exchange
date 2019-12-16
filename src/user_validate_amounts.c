#include "user_validate_amounts.h"
#include "ux.h"

#define BAGL_FONT_OPEN_SANS_LIGHT_16_22PX_AVG_WIDTH 10
#define BAGL_FONT_OPEN_SANS_REGULAR_10_13PX_AVG_WIDTH 8
#define MAX_CHAR_PER_LINE 25

#define COLOR_BG_1 0xF9F9F9
#define COLOR_APP COIN_COLOR_HDR      // bitcoin 0xFCB653
#define COLOR_APP_LIGHT COIN_COLOR_DB // bitcoin 0xFEDBA9
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

unsigned int ui_verify_message_prepro(const bagl_element_t *element) {
    if (element->component.userid > 0) {
        unsigned int display = (ux_step == element->component.userid - 1);
        if (display) {
            switch (element->component.userid) {
            case 1:
                UX_CALLBACK_SET_INTERVAL(2000);
                break;
            case 2:
                UX_CALLBACK_SET_INTERVAL(MAX(
                    3000, 1000 + bagl_label_roundtrip_duration_ms(element, 7)));
                break;
            }
        }
        return display;
    }
    return 1;
}


int user_validate_amounts(
    char* currency_from,
    unsigned char currency_from_size,
    char* currency_to,
    unsigned char currency_to_size,
    unsigned char* amount_to_provider,
    unsigned char amount_to_provider_size,
    unsigned char* amount_to_wallet,
    unsigned char amount_to_wallet_size,
    char* partner_name,
    unsigned char partner_name_size) {
    bagl_element_t ui_verify_message_signature_nanos[] = {
        UI_NANOS_BACKGROUND(),
        UI_NANOS_ICON_LEFT(0, BAGL_GLYPH_ICON_CROSS),
        UI_NANOS_ICON_RIGHT(0, BAGL_GLYPH_ICON_CHECK),
        UI_NANOS_TEXT(1, 0, 12, 128, "Sign the", BAGL_FONT_OPEN_SANS_EXTRABOLD_11px),
        UI_NANOS_TEXT(1, 0, 26, 128, "message", BAGL_FONT_OPEN_SANS_EXTRABOLD_11px),

        UI_NANOS_TEXT(2, 0, 12, 128, "Message hash", BAGL_FONT_OPEN_SANS_REGULAR_11px),
        UI_NANOS_SCROLLING_TEXT(2, 23, 26, 82, "KUKU", BAGL_FONT_OPEN_SANS_EXTRABOLD_11px)
    };
    UX_DISPLAY(ui_verify_message_signature_nanos, )
}