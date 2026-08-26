#pragma once

// These functions are not part of the transaction validation flow because they depend on the child
// library application sign result.

#ifdef HAVE_NBGL
// The "Ledger Moment" modal is only available on Stax
void display_signing_success(void);
void display_signing_failure(const char *appname);
void display_signing_exception(const char *appname);
#endif  // HAVE_NBGL
