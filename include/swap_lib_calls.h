#ifndef SWAP_LIB_CALLS
#define SWAP_LIB_CALLS

#define SIGN_TRANSACTION_IN 0x200
#define SIGN_TRANSACTION_OUT 0x201

#define GET_ADDRESS_IN 0x300
#define GET_ADDRESS_OUT 0x301

#define GET_PRINTABLE_AMOUNT_IN 0x400
#define GET_PRINTABLE_AMOUNT_OUT 0x401

// structure that should be send to specific coin application to get address
typedef struct get_address_in_parameters_s {
    unsigned char* coin_configuration;
    unsigned char coin_configuration_length;
    // serialized path, segwit, version prefix, hash used, dictionary etc. 
    // fields and serialization format depends on spesific coin app
    unsigned char* address_parameters; 
    unsigned char address_parameters_length;
    char resulted_address[50];
    char resulted_extra_id[10];
} get_address_in_parameters_t;

// structure that should be send to specific coin application to get printable amount
typedef struct get_printable_amount_in_parameters_s {
    unsigned char* coin_configuration;
    unsigned char coin_configuration_length;
    unsigned char* amount; 
    unsigned char amount_length;
    char printable_amont[30];
} get_printable_amount_in_parameters_t;



#endif