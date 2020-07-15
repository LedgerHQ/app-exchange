#ifndef _PARSE_COIN_CONFIG_H_
#define _PARSE_COIN_CONFIG_H_

int parse_coin_config(unsigned char *config, unsigned char config_length,  //
                      unsigned char **ticker,
                      unsigned char *ticker_length,                                              //
                      unsigned char **application_name, unsigned char *application_name_length,  //
                      unsigned char **pure_config, unsigned char *pure_config_length);

#endif  // _PARSE_COIN_CONFIG_H_