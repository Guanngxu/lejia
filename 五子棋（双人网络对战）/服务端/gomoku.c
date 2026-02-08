#include "gomoku.h"

void run_event_loop(int32_t epoll_fd, int32_t server_fd)
{
    struct epoll_event events[MAX_EVENTS];
    while(1) {
        // 等待事件发生
        int nfds = epoll_wait(epoll_fd, events, MAX_EVENTS, -1);
        if (nfds == -1) {
            printf("line: [%d] epoll_wait error: %s\n", __LINE__, strerror(errno));
            break;
        }

        // 处理所有发生的事件
        for (int n = 0; n < nfds; ++n) {
            if(events[n].data.fd == server_fd) {
                // 有新的客户端连接
                handle_client_accept(epoll_fd, server_fd);
            } else {
                // 处理客户端数据
                handle_client_data(epoll_fd, events[n].data.fd);
            }
        }
    }
}

// 全局客户端 ID 生成器
int16_t global_client_id = 1;
// 客户端信息数组
client_info_t *client_arr[MAX_FD] = { };
// 客户端 ID 与文件描述符映射数组
int32_t client_id_fd[MAX_FD] = { };
// 等待匹配的客户端链表头
client_info_t *wait_competitor_head = NULL;
// 等待匹配的客户端链表尾
client_info_t *wait_competitor_tail = NULL;

// 处理新的客户端连接
int32_t handle_client_accept(int32_t epoll_fd, int32_t server_fd)
{
    struct epoll_event ev;
    struct sockaddr_in client_addr;
    socklen_t len = sizeof(client_addr);

    // 接受新的客户端连接
    int32_t accept_fd = accept(server_fd, (struct sockaddr *)&client_addr, &len);
    if (accept_fd < 0) {
        printf("line: [%d] accept failed: %s\n", __LINE__, strerror(errno));
        return -1;
    }

    // 保存客户端信息
    if(client_arr[accept_fd] == NULL) {
        client_arr[accept_fd] = (client_info_t *)malloc(sizeof(client_info_t));
        
        if(client_arr[accept_fd] == NULL) {
            printf("line: [%d] malloc client_info failed: %s\n", __LINE__, strerror(errno));
            close(accept_fd);
            return -1;
        }
        
        // 新的客户端肯定没有对手
        client_arr[accept_fd]->competitor_id = 0; // 初始对手 ID 为 0
        client_arr[accept_fd]->next = NULL;
    }
    
    
    // 如果客户端不为空，则更新其信息
    client_arr[accept_fd]->fd = accept_fd;
    inet_ntop(AF_INET, &client_addr.sin_addr, client_arr[accept_fd]->ip, INET_ADDRSTRLEN);
    client_arr[accept_fd]->port = ntohs(client_addr.sin_port);
    
    printf("line: [%d] accepted new connection [fd=%d, ip=%s, port=%d, id=%d]\n", 
        __LINE__, client_arr[accept_fd]->fd, client_arr[accept_fd]->ip, client_arr[accept_fd]->port, client_arr[accept_fd]->id);
    // 将新的客户端 socket 添加到 epoll 实例中
    return epoll_add_fd(epoll_fd, accept_fd);
}

int32_t handle_report_id(int32_t fd, char *buf, ssize_t len)
{
    // 客户端上报 id，如果 id 为 0 则代表为新连接，需要分配一个新的 id
    int16_t client_id = buf[1];
    client_id = (client_id << 8) | (buf[2] & 0xFF);

    if(client_id == 0) {
        // 分配新的 id
        if(client_arr[fd]) {
            char send_buf[MSG_LEN] = {};

            client_arr[fd]->id = global_client_id++ % MAX_FD;
            printf("line: [%d] assigned new id=%d to client fd=%d\n", __LINE__, client_arr[fd]->id, fd);
            
            send_buf[0] = MSG_ASSIGN_ID;
            send_buf[1] = (client_arr[fd]->id >> 8) & 0xFF;
            send_buf[2] = client_arr[fd]->id & 0xFF;
            write(fd, send_buf, MSG_LEN);
            
            client_id_fd[client_arr[fd]->id] = fd;

            // 将客户端加入等待匹配链表
            wait_competitor_tail->next = client_arr[fd];
            wait_competitor_tail = client_arr[fd];

            // 尝试匹配客户端
            match_competitors();
        } else {
            printf("line: [%d] error: client_arr[%d] is NULL when assigning new id\n", __LINE__, fd);
            return -1;
        }
    } else {
        // 使用客户端上报的 id
        if(client_arr[fd]) {
            client_arr[fd]->id = client_id;
            client_id_fd[client_id] = fd;
            printf("line: [%d] client fd=%d reported id=%d\n", __LINE__, fd, client_id);
        } else {
            printf("line: [%d] error: client_arr[%d] is NULL when reporting id\n", __LINE__, fd);
            return -1;
        }
    }
}

int32_t match_competitors()
{
    if(wait_competitor_head->next == NULL) {
        // 没有客户端
        return -1;
    }

    client_info_t *ptr = (client_info_t *) wait_competitor_head->next;
    if(ptr->next == NULL) {
        // 只有一个客户端，无法匹配
        return -1;
    }

    client_info_t *first = wait_competitor_head->next;
    client_info_t *second = first->next;
    // 配对成功，更新双方的对手 ID
    first->competitor_id = second->id;
    second->competitor_id = first->id;

    game_judge_t *judge = (game_judge_t *) malloc(sizeof(game_judge_t));
    memset(judge, 0, sizeof(game_judge_t));
    judge->gc_count = 2; // 初始引用计数为 2，分别对应两个客户端
    first->judge = judge;
    second->judge = judge;

    first->stone_color = 1; // 黑棋
    second->stone_color = 2; // 白棋

    // 从等待匹配链表中移除已配对的客户端
    wait_competitor_head->next = second->next;
    if(wait_competitor_tail == second) {
        wait_competitor_tail = wait_competitor_head;
    }

    printf("line: [%d] matched competitors: id=%d (fd=%d) <--> id=%d (fd=%d)\n", 
        __LINE__, first->id, first->fd, second->id, second->fd);

    // 通知双方已匹配成功
    char send_buf[MSG_LEN] = {};
    send_buf[0] = MSG_GAME_START;

    send_buf[3] = first->stone_color;
    send_buf[4] = second->stone_color;
    write(first->fd, send_buf, MSG_LEN);

    send_buf[3] = second->stone_color;
    send_buf[4] = first->stone_color;
    write(second->fd, send_buf, MSG_LEN);
    return 0;
}

int32_t get_competitor_fd(int32_t client_fd)
{
    if(client_arr[client_fd] == NULL) {
        printf("line: [%d] error: client_arr[%d] is NULL when getting competitor fd\n", __LINE__, client_fd);
        return -1;
    }

    int32_t competitor_id = client_arr[client_fd]->competitor_id;
    if(competitor_id == 0) {
        printf("line: [%d] error: client fd=%d has no competitor when getting competitor fd\n", __LINE__, client_fd);
        return -1;
    }

    int32_t competitor_fd = client_id_fd[competitor_id];
    if(competitor_fd <= 0 || client_arr[competitor_fd] == NULL) {
        printf("line: [%d] error: competitor id=%d not found for client fd=%d when getting competitor fd\n", __LINE__, competitor_id, client_fd);
        return -1;
    }

    printf("line: [%d] found competitor fd=%d for client fd=%d\n", __LINE__, competitor_fd, client_fd);
    return competitor_fd;
}

int32_t handle_make_move(int32_t fd, char *buf, ssize_t len)
{
    // 查找对手的文件描述符
    int32_t competitor_fd = get_competitor_fd(fd);
    if (competitor_fd <= 0)
    {
        return -1;
    }
    
    // 更新棋盘状态
    int x = buf[3];
    int y = buf[4];
    
    // 检查落子位置是否合法
    if(client_arr[fd]->judge->board[x][y] != 0) {
        printf("line: [%d] error: client fd=%d attempted to place stone on occupied position (%d, %d)\n", __LINE__, fd, x, y);
        return -1;
    }

    client_arr[fd]->judge->board[x][y] = client_arr[fd]->stone_color;

    // 将移动请求转发给对手
    write(competitor_fd, buf, len);

    int32_t ret = check_winner(x, y, client_arr[fd]->judge);
    if(ret == 1) {
        printf("line: [%d] client fd=%d wins the game!\n", __LINE__, fd);        // 可以在这里添加通知双方游戏结束的逻辑
        buf[0] = MSG_GAME_OVER;
        buf[3] = 1; // 1 表示当前客户端获胜
        write(fd, buf, MSG_LEN); // 通知获胜方
        buf[3] = 2; // 2 表示对手获胜
        write(competitor_fd, buf, MSG_LEN); // 通知对手
    }

    printf("line: [%d] forwarded move from client fd=%d to competitor fd=%d\n", __LINE__, fd, competitor_fd);
    return 0;
}


// 代码重构
msg_type_info_t msg_typs[] = {
    {MSG_REPORT_ID, handle_report_id, "Report Client ID"},
    {MSG_MAKE_MOVE, handle_make_move, "Make a Move"},
};

void clean_client(int32_t epoll_fd, int32_t client_fd)
{
    if(client_arr[client_fd] == NULL) return;

    // 匹配链表中移除该客户端
    client_info_t *prev = wait_competitor_head;
    client_info_t *cur = wait_competitor_head->next;
    while(cur) {
        if(cur->fd == client_fd) {
            prev->next = cur->next;
            if(wait_competitor_tail == cur) {
                wait_competitor_tail = prev;
            }
            break;
        }
        prev = cur;
        cur = cur->next;
    }

    epoll_remove_fd(epoll_fd, client_fd);
    client_id_fd[client_arr[client_fd]->id] = 0;
    client_arr[client_fd]->judge->gc_count--;
    if(client_arr[client_fd]->judge->gc_count <= 0) {
        free(client_arr[client_fd]->judge);
    }
    free(client_arr[client_fd]);
    client_arr[client_fd] = NULL;
}

// 处理客户端数据
int32_t handle_client_data(int32_t epoll_fd, int32_t client_fd)
{
    char read_buf[MSG_LEN] = {};
    memset(read_buf, 0, sizeof(read_buf));
    ssize_t ret = recv(client_fd, read_buf, MSG_LEN, MSG_WAITALL);

    if (ret <= 0) {
        if(ret < 0) {
            printf("line: [%d] read error from fd=%d: %s\n", __LINE__, client_fd, strerror(errno));
        }
        else {
            printf("line: [%d] client [fd=%d] disconnected\n", __LINE__, client_fd);
        }
        // 客户端断开连接，通知对手
        char send_buf[MSG_LEN] = {};
        send_buf[0] = MSG_GAME_DISCONNECT;
        int32_t competitor_fd = get_competitor_fd(client_fd);
        if(competitor_fd > 0) {
            printf("line: [%d] notifying competitor fd=%d about disconnection of client fd=%d\n", __LINE__, competitor_fd, client_fd);
            write(competitor_fd, send_buf, MSG_LEN);
        }
        clean_client(epoll_fd, client_fd);
        return -1;
    } else {
        // 正常接收数据
        printf("line: [%d] received [%ld] data from fd=%d: %s\n", __LINE__, ret, client_fd, read_buf);
        show_hex(read_buf, ret);
        for (int32_t i = 0; i < (sizeof(msg_typs) / sizeof(msg_type_info_t)); i++) {
            if (read_buf[0] == msg_typs[i].type) {
                msg_typs[i].handler(client_fd, read_buf, ret);
                break;
            }
        }
    }
    return 0;
}

void initialize_client_list()
{
    // 初始化等待匹配的客户端链表头尾
    wait_competitor_head = (client_info_t *) malloc(sizeof(client_info_t));
    memset(wait_competitor_head, 0, sizeof(client_info_t)); // 必须清零
    wait_competitor_head->next = NULL;
    wait_competitor_tail = wait_competitor_head;
}