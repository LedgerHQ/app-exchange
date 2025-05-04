#pragma once

void ui_validate_amounts(void);

#ifdef DIRECT_CALLS_API
void direct_amount_review(const char *application_name,
                          const char *to_print,
                          const char *to_print_as_fees);
#endif  // DIRECT_CALLS_API
