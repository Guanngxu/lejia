#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define BACK_LONGTH 5 // 最大连接队列长度


int32_t tcp_server_init(int16_t port);