#include "os.h"
#include "cx.h"
#include "globals.h"
#include "string.h"

#ifndef _UTILS_H_
#define _UTILS_H_

typedef enum rlpTxType {
    TX_LENGTH = 0,
    TX_TYPE,
    TX_SENDER,
    TX_RECIPIENT,
    TX_AMOUNT,
    TX_FEE
} rlpTxType;

unsigned int ui_prepro(const bagl_element_t *element);

void sendResponse(uint8_t tx, bool approve);

int addResponseCode(unsigned char* buffer, int buffer_length, int response_code);

    // type            userid    x    y   w    h  str rad fill      fg        bg      fid iid  txt   touchparams...       ]
#define UI_BUTTONS \
    {{BAGL_RECTANGLE   , 0x00,   0,   0, 128,  32, 0, 0, BAGL_FILL, 0x000000, 0xFFFFFF, 0, 0}, NULL, 0, 0, 0, NULL, NULL, NULL},\
    {{BAGL_ICON        , 0x00,   3,  12,   7,   7, 0, 0, 0        , 0xFFFFFF, 0x000000, 0, BAGL_GLYPH_ICON_CROSS  }, NULL, 0, 0, 0, NULL, NULL, NULL },\
    {{BAGL_ICON        , 0x00, 117,  13,   8,   6, 0, 0, 0        , 0xFFFFFF, 0x000000, 0, BAGL_GLYPH_ICON_CHECK  }, NULL, 0, 0, 0, NULL, NULL, NULL }

#define UI_FIRST 1
#define UI_SECOND 0

#define UI_LABELINE(userId, text, isFirst, font, horizontalScrollSpeed)    \
    {                                                                      \
        {                                                                  \
            BAGL_LABELINE,                                                 \
            (userId),                                                      \
            23,                                                            \
            (isFirst) ? 12 : 26,                                           \
            82,                                                            \
            12,                                                            \
            (horizontalScrollSpeed) ? BAGL_STROKE_FLAG_ONESHOT | 10 : 0,   \
            0, 0, 0xFFFFFF, 0x000000,                                      \
            (font)|BAGL_FONT_ALIGNMENT_CENTER,                             \
            horizontalScrollSpeed                                          \
        },                                                                 \
        (text), 0, 0, 0, NULL, NULL, NULL                                  \
    }

#endif

// compare strings that can fill all the buffer, so without ending 0
int strcmp_non_zero(char* str1, unsigned char str1_buffer_size, char* str2, unsigned char str2_buffer_size);