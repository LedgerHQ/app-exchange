#ifndef _MENU_H_
#define _MENU_H_

void ux_init();
void ui_idle(void);

typedef void (*UserChoiseCallback)();

void ui_validate_amounts(char *send_amount, char *get_amount, char *fees_amount,
                         UserChoiseCallback on_accept, UserChoiseCallback on_reject);

#endif
