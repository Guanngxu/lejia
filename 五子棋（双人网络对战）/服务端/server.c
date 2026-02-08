#include "gomoku.h"
#include <stdlib.h>

int main(int argc, char** argv)
{
    int16_t port = 6666;
    int32_t server_fd = -1;
    int32_t epoll_fd = -1;

    if(argc == 2) {
        port = atoi(argv[1]);
    }

    server_fd = tcp_server_init(port);
    if(server_fd < 0) return -1;

    epoll_fd = epoll_init();
    if(epoll_fd < 0) {
        close(server_fd);
        return -1;
    }

    // 将服务器 socket 添加到 epoll 实例中
    if(epoll_add_fd(epoll_fd, server_fd) < 0) {
        close(server_fd);
        close(epoll_fd);
        return -1;
    }

    initialize_client_list();

    printf("Server is listening on port %d...\n", port);
    run_event_loop(epoll_fd, server_fd);

    return 0;
}