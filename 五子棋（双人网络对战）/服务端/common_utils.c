#include "common_utils.h"

/**
 * @brief 将一段数据以16进制的格式打印出来
 * @param[in] data 数据
 * @param[in] len 长度
 */
void show_hex(char *data, int32_t len)
{
    int32_t i;

    for (i = 0; i < len; i++) {
        printf("%02x ", data[i]);
    }
    printf("\n\n");
}