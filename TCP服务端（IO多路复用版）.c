#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <stdint.h>
#include <sys/epoll.h>
#include <errno.h>

#define MAX_EVENTS 1024
#define BUFFER_SIZE 1024
#define BACK_LONGTH 5 // 它限制了服务器在 accept 之前能排队的最大连接数


int32_t tcp_server_init(int16_t port)
{
    struct sockaddr_in addr = { };
    int32_t socket_fd = -1;
    int32_t opt = 1;

    // 创建 socket
    socket_fd = socket(AF_INET, SOCK_STREAM, 0);
    // 创建失败
    if (socket_fd < 0) {
        printf("create socket failed!\n");
        goto err;
    }

    setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    memset(&addr, 0, sizeof(addr)); // 初始化地址结构体
    addr.sin_port = htons(port); // 设置端口号，使用网络字节序
    addr.sin_family = AF_INET; // 使用 AF_INET 表示 IPv4 地址族
    addr.sin_addr.s_addr = htonl(INADDR_ANY); // 监听所有网卡，INADDR_ANY 表示 0.0.0.0

    // 绑定 socket 和地址
    if (bind(socket_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0){
        printf("bind error[port=%d]!\n", port);
        goto err;
    }

    // 监听端口，设置最大连接数为 BACK_LONGTH
    if (listen(socket_fd, BACK_LONGTH) < 0) {
        printf("listen error!\n");
        goto err;
    }

    return socket_fd; // 返回服务器 socket 描述符

    err:
        if (socket_fd >= 0)
            close(socket_fd);
        return -1;
}

int main()
{
    int32_t server_fd = -1;
    int32_t epoll_fd = -1;
    struct epoll_event ev, events[MAX_EVENTS];
    // epoll_event：events 表示对应的文件描述符可以读、写之类的事件类型

    // 初始化 TCP 服务器
    server_fd = tcp_server_init(6666);
    if (server_fd < 0) {
        printf("TCP server init failed!\n");
        return -1;
    }

    // 创建 epoll 实例
    epoll_fd = epoll_create1(0);
    if (epoll_fd == -1) {
        perror("epoll_create1");
        close(server_fd);
        return -1;
    }

    // 将服务器 socket 添加到 epoll 实例中
    ev.events = EPOLLIN;
    ev.data.fd = server_fd;
    // 添加 server_fd 到 epoll 实例中
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, server_fd, &ev) == -1) {
        perror("epoll_ctl: server_fd");
        close(server_fd);
        close(epoll_fd);
        return -1;
    }

    printf("Server is listening on port 6666...\n");

    while(1) {
        char buf[BUFFER_SIZE];
        // 等待事件发生
        int nfds = epoll_wait(epoll_fd, events, MAX_EVENTS, -1);
        if (nfds == -1) {
            perror("epoll_wait");
            break;
        }

        // 处理所有发生的事件
        for (int n = 0; n < nfds; ++n) {
            if(events[n].data.fd == server_fd) {
                // 有新的客户端连接
                struct sockaddr_in client_addr;
                socklen_t len = sizeof(client_addr);
                int32_t accept_fd = accept(server_fd, (struct sockaddr *)&client_addr, &len);
                if (accept_fd < 0) {
                    printf("accept failed!\n");
                    continue;
                } else {
                    // 将新的客户端 socket 添加到 epoll 实例中
                    char client_ip[INET_ADDRSTRLEN];
                    // 获取客户端 IP
                    inet_ntop(AF_INET, &client_addr.sin_addr, client_ip, INET_ADDRSTRLEN);
                    uint16_t client_port = ntohs(client_addr.sin_port);

                    ev.events = EPOLLIN; // 有事件才返回
                    ev.data.fd = accept_fd;
                    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, accept_fd, &ev) == -1) {
                        printf("epoll_ctl: accept_fd\n");
                        close(accept_fd);
                        continue;
                    }
                    printf("Accepted new connection [fd=%d, ip=%s, port=%d]\n", accept_fd, client_ip, client_port);
                    // printf("Accepted new connection [fd=%d]\n", accept_fd);
                }
            } else {
                // 处理客户端数据
                memset(buf, 0, sizeof(buf));
                int32_t client_fd = events[n].data.fd;
                ssize_t ret = read(client_fd, buf, sizeof(buf) - 1);

                if (ret < 0) {
                    perror("read error");
                    epoll_ctl(epoll_fd, EPOLL_CTL_DEL, client_fd, NULL);
                    close(client_fd);
                } else if (ret == 0) {
                    epoll_ctl(epoll_fd, EPOLL_CTL_DEL, client_fd, NULL);
                    printf("Client %d closed the connection.\n", client_fd);
                    close(client_fd);
                } else {
                    printf("recv data from [%d] %s (len=%zd)\n", client_fd, buf, ret);
                    // 回显数据
                    write(client_fd, buf, ret);
                }
            }
        }
    }

    close(server_fd);
    close(epoll_fd);
    return 0;
}