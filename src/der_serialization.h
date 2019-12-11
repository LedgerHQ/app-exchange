#ifndef _DER_SERIALIZATION_H_
#define _DER_SERIALIZATION_H_

unsigned char der_serialize(
    unsigned char* R, unsigned char r_length,
    unsigned char* S, unsigned char s_length,
    unsigned char* der, unsigned char output_buffer_size);

#endif // _DER_SERIALIZATION_H_