import pygame
import socket
import queue
import sys
import struct
import threading
from enum import IntEnum


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

# 服务器IP和端口
SERVER_IP = '8.156.83.41'
SERVER_PORT = 6666
MSG_LEN = 5  # 消息长度（字节）

# 玩家相关参数
player_id = 0

# 消息命令枚举类，定义客户端和服务器之间的消息类型
class Cmd(IntEnum):
    MSG_REPORT_ID = 1
    MSG_MAKE_MOVE = 2
    MSG_ASSIGN_ID = 3
    MSG_GAME_START = 4
    MSG_GAME_END = 5
    MSG_GAME_DISCONNECT = 6

class TCPClient:
    """TCP客户端类，负责网络通信"""
    
    def __init__(self, game_callback):
        """初始化TCP客户端并连接服务器"""
        self.game_callback = game_callback  # 游戏回调函数
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP套接字
        self.socket.connect((SERVER_IP, SERVER_PORT))          # 连接服务器
        print(f"已连接到服务器 {SERVER_IP}:{SERVER_PORT}")

        self.report_id()  # 向服务器报告玩家ID
        threading.Thread(target=self.recv_loop, daemon=True).start()  # 启动接收线程
        print("启动接收线程")

    def send_msg(self, cmd, x=0, y=0):
        global player_id
        send_data = struct.pack('!BHBB', cmd, player_id, x, y)
        self.socket.sendall(send_data)
        print(f"发送消息: cmd={cmd}, id={player_id}, x={x}, y={y}")

    def report_id(self):
        self.send_msg(Cmd.MSG_REPORT_ID)

    def recv_loop(self):
        while True:
            data = self.socket.recv(MSG_LEN)
            if not data:
                print("服务器断开连接")
                break
            cmd, p_id, x, y = struct.unpack('!BHBB', data)
            self.game_callback(cmd, p_id, x, y)
        

class GomokuGame:
    """游戏主类，负责游戏流程控制和界面显示"""
    
    def __init__(self):
        """初始化游戏"""
        pygame.init()  # 初始化Pygame所有模块
        self.window = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        self.msg_queue = queue.Queue()
        self.msg_queue.put(("MSG", "五子棋双人对战")) # 设置窗口标题
        # 字体初始化
        self.font = pygame.font.SysFont("SimHei", 24) # 使用黑体
        self.msg_queue.put(("MSG", "正在连接服务器..."))
        # 当前回合的棋子颜色，1=黑棋（玩家先手），2=白棋（AI）
        self.tcp = TCPClient(self.tcp_callback)
        self.my_color = 0 # 玩家棋子颜色
        self.competitor_color = 0  # 对手棋子颜色
        self.my_turn = False  # 是否轮到玩家下棋
        self.draw_board() # 绘制初始棋盘

    def set_title(self, msg):
        """设置窗口标题"""
        pygame.display.set_caption(msg)

    def tcp_callback(self, cmd, p_id, x, y):
        print(f"收到服务器消息: cmd={cmd}, id={p_id}, x={x}, y={y}")
        global player_id
        if cmd == Cmd.MSG_ASSIGN_ID:
            player_id = p_id
            self.msg_queue.put(("MSG", f"已连接(ID:{player_id})，等待匹配对手..."))
            print(f"分配玩家 ID: {player_id}")
        elif cmd == Cmd.MSG_GAME_START:
            print("游戏开始：", "你执黑先手" if x == 1 else "你执白后手")
            color_name = "黑棋(先手)" if x == 1 else "白棋(后手)"
            self.msg_queue.put(("MSG", f"匹配成功！你执{color_name}"))
            self.my_color = x  # 游戏开始，玩家执黑先手
            self.competitor_color = y  # 对手颜色
            if self.my_color == 1:
                self.msg_queue.put(("MSG", "轮到你下棋..."))
                self.my_turn = True
        elif cmd == Cmd.MSG_MAKE_MOVE:
            print(f"对手落子: ({x}, {y})")
            self.msg_queue.put(("MOVE", x, y, self.competitor_color))
            # 轮到玩家下棋
            self.my_turn = True
            self.msg_queue.put(("MSG", "轮到你下棋..."))
        elif cmd == Cmd.MSG_GAME_END:
            if x == 1:
                self.msg_queue.put(("MSG", "您赢了！！！"))
            else:
                self.msg_queue.put(("MSG", "您输了！！！"))
            self.my_turn = False
        elif cmd == Cmd.MSG_GAME_DISCONNECT:
            self.msg_queue.put(("MSG", "对手掉线了"))
            



    def main_loop(self):
        """游戏主循环，不断处理事件和更新画面"""
        while True:  # 无限循环，直到游戏退出
            pygame.time.Clock().tick(60)  # 控制帧率为60FPS
            # 处理消息队列中的消息
            while not self.msg_queue.empty():
                msg = self.msg_queue.get()
                if msg[0] == "MSG":
                    self.set_title(msg[1])
                elif msg[0] == "MOVE":
                    x, y, color = msg[1], msg[2], msg[3]
                    self.make_move(x, y, color)

            # 获取所有发生的事件（鼠标点击、窗口关闭等）
            for event in pygame.event.get():
                # 如果事件是关闭窗口（点击右上角的X）
                if event.type == pygame.QUIT:
                    pygame.quit()  # 关闭Pygame
                    sys.exit()     # 退出程序
                
                # 如果事件是鼠标按钮按下（玩家点击落子）
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.my_turn:
                        # 获取鼠标点击的像素坐标
                        x, y = event.pos
                        # 将像素坐标转换为棋盘网格坐标
                        grid_x, grid_y = self.compute_grid_position(x, y)
                        # 处理玩家落子
                        self.msg_queue.put(("MOVE", grid_x, grid_y, self.my_color))
                        # self.make_move(grid_x, grid_y, self.my_color)
                        # 通知玩家已落子
                        self.msg_queue.put(("MSG", f"对方回合，等待对手落子..."))
                        self.tcp.send_msg(Cmd.MSG_MAKE_MOVE, grid_x, grid_y)  # 向服务器发送落子消息
                        # 落子后轮到对手
                        self.my_turn = False
            
            # 更新整个游戏窗口的显示
            pygame.display.update()
    
    def make_move(self, grid_x, grid_y, color):
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
            # 在棋盘上绘制棋子
            self.place_stone(grid_x, grid_y, color)
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

def main():
    """程序主入口函数"""
    # 创建游戏对象
    game = GomokuGame()
    # 开始游戏主循环
    game.main_loop()

# Python程序的入口点
# 当直接运行这个文件时，__name__等于"__main__"
# 当被导入为模块时，__name__等于模块名
if __name__ == "__main__":
    main() # 调用主函数开始游戏