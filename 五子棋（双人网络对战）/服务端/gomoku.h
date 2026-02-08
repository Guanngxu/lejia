#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>

#include "epoll_utils.h"
#include "tcp_utils.h"
#include "common_utils.h"
#include "judge.h"

#define MAX_EVENTS 1024 // 最大事件数
#define BUFFER_SIZE 1024 // 缓冲区大小
#define MAX_FD 1024 // 最大文件描述符数量
#define MSG_LEN 5 // 消息长度

typedef struct {
    int32_t fd;
    int32_t competitor_id;
    int16_t port;
    int16_t id;
    char stone_color; // 'B' 或 'W'
    char ip[INET_ADDRSTRLEN];
    void *next;
    game_judge_t *judge; // 指向棋盘结构体
} client_info_t;

typedef enum {
    MSG_REPORT_ID = 0x01,
    MSG_MAKE_MOVE = 0x02,
    MSG_ASSIGN_ID = 0x03,
    MSG_GAME_START = 0x04,
    MSG_GAME_OVER = 0x05,
    MSG_GAME_DISCONNECT = 0x06,
} msg_type_t;

// 函数指针类型，处理消息的函数签名
typedef int32_t (*msg_handler)(int32_t client_fd, char *buf, ssize_t len);
// 定义一类函数的类型

typedef struct {
	char type;
	msg_handler handler;
	char *desc;
} msg_type_info_t;


// 处理新的客户端连接
int32_t handle_client_accept(int32_t epoll_fd, int32_t server_fd);

int32_t handle_report_id(int32_t fd, char *buf, ssize_t len);

int32_t match_competitors();

int32_t handle_make_move(int32_t fd, char *buf, ssize_t len);
// 处理客户端数据
int32_t handle_client_data(int32_t epoll_fd, int32_t client_fd);

void clean_client(int32_t epoll_fd, int32_t client_fd);

void run_event_loop(int32_t epoll_fd, int32_t server_fd);

void initialize_client_list();

int32_t get_competitor_fd(int32_t client_fd);