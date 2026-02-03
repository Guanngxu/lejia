import pygame
import sys
import time
import threading
from tkinter import Tk, messagebox

# 窗口大小（像素）
WINDOW_SIZE = 736

# 棋盘大小（16x16，包含边框）
BOARD_SIZE = 16

# 棋子半径（像素）
STONE_SIZE = 15

# 总的获胜模式数量（所有可能的五子连珠方向）
# 公式解释：棋盘有4个方向（横、竖、两个斜向）
# 每个方向在棋盘上可以放置的位置数量
TOTAL_WIN_PATTERNS = 4 * (BOARD_SIZE - 4) * (BOARD_SIZE - 2)

# 网格间距（每个格子的大小）
GAP = WINDOW_SIZE // BOARD_SIZE

# 棋盘上的五个星位点（传统五子棋的标准位置）
# 坐标从0开始，对应棋盘上的交叉点
POINTS = [(2, 2), (2, 12), (7, 7), (12, 2), (12, 12)]

# 颜色定义（使用RGB格式）
COLORS = {
    "background": (240, 217, 181),  # 背景色（米黄色）
    "line": (0, 0, 0),              # 棋盘线颜色（黑色）
    "black_stone": (0, 0, 0),       # 黑棋颜色
    "white_stone": (255, 255, 255), # 白棋颜色
}

# 注意：实际项目中应尽量避免使用全局变量，这里为了简化而使用
# 线程锁：用于多线程同步，防止多个线程同时访问共享资源
lock = threading.Lock()

# 弹窗状态：标记是否已经弹出获胜提示窗口
show_popup_window = False

# 获胜者：记录游戏获胜方（玩家或AI）
winner = None

class GomokuGame:
    """游戏主类，负责游戏流程控制和界面显示"""
    
    def __init__(self):
        """初始化游戏"""
        pygame.init()  # 初始化Pygame所有模块
        
        # 创建游戏窗口，大小为WINDOW_SIZE × WINDOW_SIZE
        self.window = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))

        pygame.display.set_caption("五子棋双人对战") # 设置窗口标题
        
        self.judge = Judge() # 创建裁判对象
        
        # 当前回合的棋子颜色，1=黑棋（玩家先手），2=白棋（AI）
        self.cur_color = 1

        self.draw_board() # 绘制初始棋盘

    def main_loop(self):
        """游戏主循环，不断处理事件和更新画面"""
        while True:  # 无限循环，直到游戏退出
            # 获取所有发生的事件（鼠标点击、窗口关闭等）
            for event in pygame.event.get():
                # 如果事件是关闭窗口（点击右上角的X）
                if event.type == pygame.QUIT:
                    pygame.quit()  # 关闭Pygame
                    sys.exit()     # 退出程序
                
                # 如果事件是鼠标按钮按下（玩家点击落子）
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # 获取鼠标点击的像素坐标
                    x, y = event.pos
                    
                    # 将像素坐标转换为棋盘网格坐标
                    grid_x, grid_y = self.compute_grid_position(x, y)
                    
                    # 处理玩家落子
                    self.make_move(grid_x, grid_y)
            
            # 更新整个游戏窗口的显示
            pygame.display.update()
    
    def make_move(self, grid_x, grid_y):
        """
        处理棋子落子，包括玩家和AI
        
        参数:
            grid_x: 网格行坐标
            grid_y: 网格列坐标
            
        返回:
            True: 落子成功
            False: 落子失败（位置无效或已有棋子）
        """
        # 检查坐标是否在有效范围内（1 到 BOARD_SIZE-1）
        if 0 < grid_x < BOARD_SIZE and 0 < grid_y < BOARD_SIZE:
            # 检查这个位置是否为空
            if self.judge.board[grid_x][grid_y] == 0:
                # 在棋盘上绘制棋子
                self.place_stone(grid_x, grid_y, self.cur_color)
                
                # 更新棋盘状态，并检查是否获胜
                self.judge.update_board(grid_x, grid_y, self.cur_color)
                
                # 切换当前回合：黑棋变白棋，白棋变黑棋
                self.cur_color = 2 if self.cur_color == 1 else 1
                
                return True  # 落子成功
        
        return False  # 落子失败

    def place_stone(self, grid_x, grid_y, color):
        """
        在棋盘上绘制一个棋子
        
        参数:
            grid_x: 网格行坐标
            grid_y: 网格列坐标
            color: 棋子颜色，1=黑棋，2=白棋
        """
        # 根据颜色选择棋子颜色
        stone_color = COLORS["black_stone"] if color == 1 else COLORS["white_stone"]
        # 绘制圆形棋子
        pygame.draw.circle(self.window, stone_color, (grid_x * GAP, grid_y * GAP), STONE_SIZE)
    
    def compute_grid_position(self, x, y):
        """
        将鼠标点击的像素坐标转换为棋盘网格坐标
        
        参数:
            x: 像素X坐标
            y: 像素Y坐标
            
        返回:
            (grid_x, grid_y): 网格坐标
        """
        # 计算最近的网格坐标：像素坐标 ÷ 网格间距，四舍五入
        grid_x = round(x / GAP)
        grid_y = round(y / GAP)
        
        # 确保坐标在有效范围内（1到BOARD_SIZE-1）
        grid_x = max(1, min(BOARD_SIZE - 1, grid_x))
        grid_y = max(1, min(BOARD_SIZE - 1, grid_y))

        return grid_x, grid_y
    
    def draw_board(self):
        """绘制棋盘背景、网格线和星位点"""
        # 填充背景颜色
        self.window.fill(COLORS["background"])
        
        # 绘制棋盘网格线
        for i in range(BOARD_SIZE):
            # 绘制水平线：从左到右
            pygame.draw.line(self.window, COLORS["line"],  # 表面, 颜色
                            (GAP, GAP * (i + 1)),          # 起点坐标
                            (WINDOW_SIZE - GAP, GAP * (i + 1)),  # 终点坐标
                            1)                             # 线宽（像素）
            
            # 绘制垂直线：从上到下
            pygame.draw.line(self.window, COLORS["line"],  # 表面, 颜色
                            (GAP * (i + 1), GAP),          # 起点坐标
                            (GAP * (i + 1), WINDOW_SIZE - GAP),  # 终点坐标
                            1)                             # 线宽
            
        # 绘制五个星位点（棋盘上的小黑点）
        for point in POINTS:
            # 计算星位点的像素坐标
            # point[0]和point[1]是网格坐标，需要转换为像素坐标
            # 注意：point坐标是0-based，但棋盘有边框，所以要+1
            pixel_x = GAP * (point[0] + 1)
            pixel_y = GAP * (point[1] + 1)
            
            # 绘制小黑点：表面, 颜色, 圆心坐标, 半径
            pygame.draw.circle(self.window, COLORS["line"], 
                              (pixel_x, pixel_y), 5)

class Judge:
    """裁判类，负责管理棋盘状态和判断胜负"""
    
    def __init__(self):
        """初始化棋盘"""
        # 创建棋盘二维数组，所有位置初始化为0（空）
        # 棋盘大小：BOARD_SIZE × BOARD_SIZE（第1行和第一列没有使用）
        # 0 = 空，1 = 黑棋（玩家），2 = 白棋（AI）
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    
    def update_board(self, x, y, color):
        """
        更新棋盘并检查游戏是否结束
        
        参数:
            x: 落子的行坐标
            y: 落子的列坐标
            color: 棋子颜色，1或2
            
        返回:
            True: 更新成功
            False: 更新失败（传入位置有棋子）
        """

        # 检查要落子的位置是否为空
        if self.board[x][y] == 0:
            # 在棋盘上放置棋子
            self.board[x][y] = color
            
            # 检查是否获胜（五子连珠）
            if self.check_win(x, y):
                # 使用全局变量记录获胜信息
                global show_popup_window, winner
                with lock: # 加锁，确保线程安全
                    show_popup_window = True # 设置弹窗标志

                    # 确定获胜者：1=玩家，2=AI
                    winner = "玩家 (黑色)" if color == 1 else "AI (白色)"

            # 检查是否平局（棋盘满了）
            if self.is_full():
                show_popup_window = True

            # 返回更新成功
            return True
        # 位置已有棋子，更新失败
        return False
    
    def check_win(self, x, y):
        """
        检查是否五子连珠（获胜条件）
        
        参数:
            x: 最后落子的行坐标
            y: 最后落子的列坐标
            
        返回:
            True: 有五子连珠，获胜
            False: 没有五子连珠
        """
        # 四个检查方向：(行增量, 列增量)
        directions = [(1, 0),   # 水平方向（右/左）
                      (0, 1),   # 垂直方向（下/上）
                      (1, 1),   # 右下/左上对角线
                      (1, -1)]  # 左下/右上对角线
        
        # 获取最后落子的颜色
        cur_color = self.board[x][y]
        
        # 检查每个方向
        for dx, dy in directions:
            stone_count = 1  # 从当前棋子开始计数，初始为1
            
            # 向两个方向检查：正向和反向
            for sign in (1, -1):
                # 从当前位置向指定方向移动一步
                cur_x, cur_y = x + dx * sign, y + dy * sign
                
                # 沿着这个方向连续检查相同颜色的棋子
                while (0 < cur_x < BOARD_SIZE and      # 检查行坐标是否在边界内
                       0 < cur_y < BOARD_SIZE and      # 检查列坐标是否在边界内
                       self.board[cur_x][cur_y] == cur_color):  # 检查颜色是否相同
                    stone_count += 1  # 发现相同颜色棋子，计数加1
                    # 继续向同一方向移动，检查下一个位置
                    cur_x += dx * sign
                    cur_y += dy * sign
            
            # 如果连续相同颜色的棋子数达到5个，获胜！
            if stone_count >= 5:
                return True
        
        # 所有方向都检查完毕，没有找到五子连珠
        return False
    
    def is_full(self):
        """
        检查棋盘是否已满（平局条件）
        
        返回:
            True: 棋盘已满，平局
            False: 棋盘还有空位
        """
        # 遍历棋盘的每一行
        for row in self.board:
            # 检查这一行是否还有空位（0表示空位）
            if 0 in row:
                return False  # 发现空位，棋盘未满
        
        # 所有位置都非空，棋盘已满
        return True

class PopupWindow(Tk):
    """弹窗类，用于显示游戏结果提示"""
    
    def __init__(self):
        """初始化弹窗窗口"""
        # 调用父类Tk的初始化方法
        super().__init__()
        # 隐藏主窗口，我们只需要消息框
        self.wm_withdraw()
    
    def show_message(self, msg):
        """
        显示消息框
        
        参数:
            msg: 要显示的消息内容
        """
        # 使用tkinter的messagebox显示提示信息
        # "提示！！！"是窗口标题，msg是具体内容
        messagebox.showinfo("提示！！！", msg)


def show_winner_popup():
    """
    显示获胜弹窗的线程函数
    
    这个函数在一个单独的线程中运行，定期检查是否需要显示获胜提示。
    使用多线程可以避免弹窗阻塞游戏主循环。
    """
    # 声明使用全局变量
    global show_popup_window, winner
    
    # 无限循环，持续检查是否需要显示弹窗
    while True:
        # 使用线程锁，确保安全访问全局变量
        with lock:
            # 检查是否需要显示弹窗
            if show_popup_window:
                # 创建弹窗对象
                popup = PopupWindow()
                
                # 根据获胜者显示不同的消息
                if winner:  # winner不为None，表示有获胜者
                    popup.show_message(f"{winner} 获胜!")
                else:       # winner为None，表示平局
                    popup.show_message("平局！")
                
                # 重置弹窗标志，避免重复显示
                show_popup_window = False
                
                # 退出循环（弹窗已经显示）
                break
        
        # 暂停0.5秒再检查，避免过度占用CPU
        time.sleep(0.5)

def main():
    """程序主入口函数"""
    # 创建游戏对象
    game = GomokuGame()
    
    # 创建并启动弹窗线程
    # target: 线程要执行的函数
    # daemon=True: 设置为守护线程，主程序退出时自动结束
    popup_thread = threading.Thread(target=show_winner_popup, daemon=True)
    popup_thread.start()  # 启动线程
    
    # 开始游戏主循环
    game.main_loop()

# Python程序的入口点
# 当直接运行这个文件时，__name__等于"__main__"
# 当被导入为模块时，__name__等于模块名
if __name__ == "__main__":
    main() # 调用主函数开始游戏