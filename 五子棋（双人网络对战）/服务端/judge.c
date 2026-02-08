#include "judge.h"


/**
 * 检查是否五子连珠
 * @param x 最后落子的行坐标
 * @param y 最后落子的列坐标
 * @param board 棋盘数组 (0:无子, 1:黑子, 2:白子)
 * @return 1 表示获胜，0 表示未获胜
 */
int32_t check_winner(int32_t x, int32_t y, game_judge_t *game_judge) 
{
    // 获取当前落子的颜色
    int32_t cur_color = game_judge->board[x][y];
    if (cur_color == 0) return 0; // 如果该位置没棋子，直接返回

    // 四个检查方向：水平、垂直、右下对角线、左下对角线
    int32_t dx[] = {1, 0, 1, 1};
    int32_t dy[] = {0, 1, 1, -1};

    // 检查 4 个轴向
    for (int32_t i = 0; i < 4; i++) {
        int32_t stone_count = 1; // 初始计数为 1（当前落子）

        // 每个轴向检查两个相反的方向 (正向和反向)
        for (int32_t sign = 1; sign >= -1; sign -= 2) {
            int32_t cur_x = x + dx[i] * sign;
            int32_t cur_y = y + dy[i] * sign;

            // 沿着该方向连续检查
            while (cur_x >= 0 && cur_x < BOARD_SIZE &&
                   cur_y >= 0 && cur_y < BOARD_SIZE &&
                   game_judge->board[cur_x][cur_y] == cur_color) {
                
                stone_count++;
                cur_x += dx[i] * sign;
                cur_y += dy[i] * sign;
            }
        }

        // 如果该轴向上连续棋子数 >= 5，判定获胜
        if (stone_count >= 5) {
            return 1;
        }
    }

    return 0; // 所有方向检查完毕，没有五连
}