#!/bin/bash
# build.sh - 构建五子棋（双人网络对战）服务端
# 作者: guanngxu
# 日期: $(date +"%Y-%m-%d")
# 用法: bash build.sh
rm -f server
gcc server.c common_utils.c epoll_utils.c tcp_utils.c judge.c gomoku.c -o server