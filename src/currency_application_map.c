#include "currency_application_map.h"
#include "string.h"

#define MAP_SIZE 10

char currency_application_map[MAP_SIZE][2][30] = {
    {"Bitcoin", "Bitcoin"}};

char* get_application_name(char* currency) {
    for (int i = 0; i < MAP_SIZE; ++i) {
        if (currency_application_map[i][0] == 0)
            return 0;
        if (strcmp(currency, currency_application_map[i][0]) == 0) {
            return currency_application_map[i][1];
        }
    }
    return 0;
}
