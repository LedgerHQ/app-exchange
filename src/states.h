#ifndef _STATES_H
#define _STATES_H

typedef enum {
    INITIAL_STATE                   = 1,
    WAITING_TRANSACTION             = 2,
    PROVIDER_SETTED                 = 3,
    TRANSACTION_RECIEVED            = 5,
    STATE_UPPER_BOUND
} state_e;

#endif //_STATES_H