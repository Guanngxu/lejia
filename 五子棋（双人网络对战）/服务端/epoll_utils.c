#include "epoll_utils.h"

// 初始化 epoll 实例，返回 epoll 文件描述符
int32_t epoll_init()
{
    int32_t epoll_fd = -1;
    // 创建 epoll 实例
    epoll_fd = epoll_create1(0);
    if (epoll_fd == -1) {
        printf("line: [%d] epoll_create1 error: %s\n", __LINE__, strerror(errno));
        return -1;
    }
    return epoll_fd;
}

// 将文件描述符添加到 epoll 实例中
int32_t epoll_add_fd(int32_t epoll_fd, int32_t fd)
{
    struct epoll_event ev;
    ev.events = EPOLLIN; // 有事件才返回
    ev.data.fd = fd;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, fd, &ev) == -1) {
        printf("line: [%d] epoll_ctl ADD error: %s\n", __LINE__, strerror(errno));
        return -1;
    }
    return 0;
}

// 从 epoll 实例中移除文件描述符
void epoll_remove_fd(int32_t epoll_fd, int32_t fd)
{
    epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL);
    close(fd);
}