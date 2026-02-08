#include "tcp_utils.h"


// 初始化 TCP 服务器，返回服务器 socket 描述符
int32_t tcp_server_init(int16_t port)
{
    struct sockaddr_in addr = {}; // 服务器地址结构体
    int32_t server_fd = -1; // 服务器 socket 描述符
    int32_t opt = 1; // 端口复用选项

    // 创建 socket，该函数创建的是主动套接字
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        printf("line: [%d] create socket failed: %s\n", __LINE__, strerror(errno));
        goto err;
    }

    // 设置端口复用
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    memset(&addr, 0, sizeof(addr)); // 初始化地址结构体
    addr.sin_port = htons(port); // 设置端口号，使用网络字节序
    addr.sin_family = AF_INET; // 使用 AF_INET 表示 IPv4 地址族
    addr.sin_addr.s_addr = htonl(INADDR_ANY); // 监听所有网卡，INADDR_ANY 表示 0.0.0.0

    // 绑定 socket 和地址
    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0){
        printf("line: [%d] bind error[port=%d]: %s\n", __LINE__, port, strerror(errno));
        goto err;
    }

    // 监听端口，设置最大连接数为 BACK_LONGTH
    // 将主动套接字变为被动套接字
    if (listen(server_fd, BACK_LONGTH) < 0) {
        printf("line: [%d] listen error: %s\n", __LINE__, strerror(errno));
        goto err;
    }

    return server_fd; // 返回服务器 socket 描述符

    err:
        if (server_fd >= 0)
            close(server_fd);
        return -1;
}
