#ifndef _STATES_H_
#define _STATES_H_

typedef enum {
    INITIAL_STATE                   = 0,
    WAITING_TRANSACTION             = 1,
    PROVIDER_SET                    = 2,
    TRANSACTION_RECIEVED            = 3,
    SIGNATURE_CHECKED               = 4,
    TO_ADDR_CHECKED                 = 5,
    WAITING_USER_VALIDATION         = 6,
    STATE_UPPER_BOUND
} state_e;

#endif //_STATES_H_