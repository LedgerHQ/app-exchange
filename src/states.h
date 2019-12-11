#ifndef _STATES_H_
#define _STATES_H_

typedef enum {
    INITIAL_STATE                   = 1,
    WAITING_TRANSACTION             = 2,
    PROVIDER_SETTED                 = 3,
    TRANSACTION_RECIEVED            = 4,
    SIGNATURE_CHECKED               = 5,
    TO_ADDR_CHECKED                 = 6,
    STATE_UPPER_BOUND
} state_e;

#endif //_STATES_H_