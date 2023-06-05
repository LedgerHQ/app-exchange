#pragma once

void ui_validate_amounts(void);

#ifdef HAVE_NBGL
// The "Ledger Moment" modal is only available on Stax
void display_signing_success(void);
void display_signing_failure(const char *appname);
#endif
