#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <stdint.h>

#define BACK_LONGTH 5
#define BUFFER_SIZE 1024

// 定义传递给线程的参数结构体
typedef struct {
    int32_t fd;
    struct sockaddr_in addr;
} client_info_t;

// 线程处理函数：负责与特定客户端通信
void *handle_client(void *arg) {
    client_info_t *info = (client_info_t *)arg;
    int32_t client_fd = info->fd;
    char client_ip[INET_ADDRSTRLEN];
    
    // 获取客户端 IP
    inet_ntop(AF_INET, &info->addr.sin_addr, client_ip, INET_ADDRSTRLEN);
    uint16_t client_port = ntohs(info->addr.sin_port);

    printf("[Thread %lu] Started handling client %s:%d\n", pthread_self(), client_ip, client_port);

    char buf[BUFFER_SIZE];
    while (1) {
        memset(buf, 0, sizeof(buf));
        ssize_t ret = read(client_fd, buf, sizeof(buf) - 1);

        if (ret < 0) {
            perror("read error");
            break;
        } else if (ret == 0) {
            printf("Client %s:%d closed the connection.\n", client_ip, client_port);
            break;
        } else {
            printf("From %s:%d: %s (len=%zd)\n", client_ip, client_port, buf, ret);
            // 回显数据
            // write(client_fd, buf, ret);
        }
    }

    close(client_fd);
    free(info); // 释放主线程申请的内存
    printf("[Thread %lu] Finished.\n", pthread_self());
    return NULL;
}

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
    
    // 初始化 TCP 服务器
    server_fd = tcp_server_init(6666);
    if (server_fd < 0) {
        printf("TCP server init failed!\n");
        return -1;
    }

    while(1) {
        struct sockaddr_in client_addr;
        int32_t accept_fd = -1;
        socklen_t len = sizeof(client_addr);
        
        // 每次 accept 前必须重新初始化地址长度
        len = sizeof(client_addr);
        memset(&client_addr, 0, sizeof(client_addr));

        // 接受客户端连接，程序会在此阻塞，直到有客户端连接进来
        accept_fd = accept(server_fd, (struct sockaddr *)&client_addr, &len);
        if (accept_fd < 0) {
            printf("accept failed!\n");
            close(server_fd);
            return -1;
        }

        // 为每个新连接动态分配内存，防止竞争条件
        client_info_t *info = malloc(sizeof(client_info_t));
        info->fd = accept_fd;
        info->addr = client_addr;

        pthread_t tid;
        // 创建线程
        if (pthread_create(&tid, NULL, handle_client, (void *)info) != 0) {
            perror("Thread creation failed");
            close(accept_fd);
            free(info);
        } else {
            // 设置线程为分离模式，线程结束后自动回收资源，无需 pthread_join
            pthread_detach(tid);
        }
    }
    close(server_fd);

    return 0;
}