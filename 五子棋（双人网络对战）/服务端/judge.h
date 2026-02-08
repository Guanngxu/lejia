#include <stdint.h>

#define BOARD_SIZE 16

typedef struct {
    char board[BOARD_SIZE][BOARD_SIZE];
    char gc_count;// 引用计数
} game_judge_t;


int32_t check_winner(int32_t x, int32_t y, game_judge_t *game_judge);