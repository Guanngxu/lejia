#include <sys/epoll.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>

// 初始化 epoll 实例，返回 epoll 文件描述符
int32_t epoll_init();

// 将文件描述符添加到 epoll 实例中
int32_t epoll_add_fd(int32_t epoll_fd, int32_t fd);

// 从 epoll 实例中移除文件描述符
void epoll_remove_fd(int32_t epoll_fd, int32_t fd);