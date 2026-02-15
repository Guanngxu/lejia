import pygame
import socket
import queue
import time
import sys
import struct
import threading
from enum import IntEnum


WINDOW_SIZE = 736
BOARD_SIZE = 16
STONE_SIZE = 15
CONNECTED_TIME = 6 * 3
TOTAL_WIN_PATTERNS = 4 * (BOARD_SIZE - 4) * (BOARD_SIZE - 2)
GAP = WINDOW_SIZE // BOARD_SIZE
POINTS = [(2, 2), (2, 12), (7, 7), (12, 2), (12, 12)]
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

class Cmd(IntEnum):
    MSG_REPORT_ID = 1
    MSG_MAKE_MOVE = 2
    MSG_ASSIGN_ID = 3
    MSG_GAME_START = 4
    MSG_GAME_END = 5
    MSG_GAME_DISCONNECT = 6

class StoneColor(IntEnum):
    BLACK = 1
    WHITE = 2

class GameMode(IntEnum):
    NETWORK = 1
    LOCAL_AI = 2

class TCPClient:
    """TCP客户端类，负责网络通信"""
    
    def __init__(self, game_callback, timeout_callback):
        """初始化TCP客户端并连接服务器"""
        self.game_callback = game_callback  # 游戏回调函数
        self.timeout_callback = timeout_callback
        self.connected = False
        self.is_matched = False
        self.start_time = time.time()
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP套接字
            self.socket.connect((SERVER_IP, SERVER_PORT))          # 连接服务器
            self.connected = True
            print(f"已连接到服务器 {SERVER_IP}:{SERVER_PORT}")

            self.report_id()  # 向服务器报告玩家ID
            print("启动接收线程")
            threading.Thread(target=self.recv_loop, daemon=True).start()  # 启动接收线程
            threading.Thread(target=self.check_time, daemon=True).start() # 启动超时检查线程
        except Exception as e:
            print(f"连接服务器失败：{e}")
            self.timeout_callback()

    def disconnect(self):
        if self.socket:
            try:
                # 这会给服务器发送一个 FIN 包，优雅地告诉对方：我要走了
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except Exception as e:
                print(f"断开连接异常: {e}")
            finally:
                self.socket = None
                self.connected = False

    def check_time(self):
        while self.connected:
            # 如果已经匹配成功，直接退出计时线程，不再监控超时
            if self.is_matched:
                print("匹配成功，停止超时监控")
                break

            elapsed_time = time.time() - self.start_time
            if elapsed_time > CONNECTED_TIME:
                self.connected = False
                self.timeout_callback()
                break
            time.sleep(1)

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


class Judge:

    def __init__(self):
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    
    def update_board(self, x, y, color):
        if self.board[x][y] == 0:
            self.board[x][y] = color
            if self.check_win(x, y):
                return color
    
    def check_win(self, x, y):
        # 四个检查方向：(行增量, 列增量)
        directions = [(1, 0),   # 水平方向（右/左）
                      (0, 1),   # 垂直方向（下/上）
                      (1, 1),   # 右下/左上对角线
                      (1, -1)]  # 左下/右上对角线
        cur_color = self.board[x][y]
        for dx, dy in directions:
            stone_count = 1
            for sign in (1, -1):
                cur_x, cur_y = x + dx * sign, y + dy * sign
                while (0 < cur_x < BOARD_SIZE and
                       0 < cur_y < BOARD_SIZE and
                       self.board[cur_x][cur_y] == cur_color):
                    stone_count += 1
                    cur_x += dx * sign
                    cur_y += dy * sign
            if stone_count >= 5:
                return True
        return False
    
    def is_full(self):
        for row in self.board:
            if 0 in row:
                return False
        return True

class AI:

    def __init__(self):
        """初始化AI"""
        self.win_patterns = [[[False for _ in range(TOTAL_WIN_PATTERNS)] 
                     for _ in range(BOARD_SIZE)] 
                     for _ in range(BOARD_SIZE)]
        self.ai_win_count = [0 for _ in range(TOTAL_WIN_PATTERNS)]
        self.human_win_count = [0 for _ in range(TOTAL_WIN_PATTERNS)]

        self.win_pattern_count = 0
        self.human_score_weights = {
            1: 200,    # 单独一子
            2: 400,    # 两子连珠
            3: 2000,   # 三子连珠
            4: 10000,  # 四子连珠（差一子获胜）
        }
        self.ai_score_weights = {
            1: 220,    # 比玩家略高
            2: 420,
            3: 2100,
            4: 20000,  # 四子连珠得分远高于玩家
        }
        self.init_win_patterns()
    
    def add_win_pattern(self, start_i, start_j, di, dj):
        for k in range(5):
            self.win_patterns[start_i + k * di][start_j + k * dj][self.win_pattern_count] = True
        self.win_pattern_count += 1

    def init_win_patterns(self):
        # 横向和纵向的所有赢法
        for i in range(1, BOARD_SIZE):
            for j in range(1, BOARD_SIZE - 4):
                # 水平方向的获胜模式
                self.add_win_pattern(i, j, 0, 1)
                # 垂直方向的获胜模式
                self.add_win_pattern(j, i, 1, 0)
        
        # 对角线方向的所有赢法
        for i in range(1, BOARD_SIZE - 4):
            for j in range(1, BOARD_SIZE - 4):
                # 右下对角线获胜模式
                self.add_win_pattern(i, j, 1, 1)
                # 左下对角线获胜模式
                self.add_win_pattern(i, BOARD_SIZE - j, 1, -1)
    
    def update_win_counts(self, x, y, color):
        # 遍历所有获胜模式
        for k in range(TOTAL_WIN_PATTERNS):
            # 检查这个位置是否属于第k个获胜模式
            if self.win_patterns[x][y][k]:
                if color == StoneColor.WHITE:  # AI下棋（白棋）
                    # AI在这个获胜模式中增加一子
                    self.ai_win_count[k] += 1
                    # 玩家在这个模式中不可能获胜了（设置为异常值6，超过5）
                    self.human_win_count[k] = 6
                else:  # 玩家下棋（黑棋）
                    # 玩家在这个获胜模式中增加一子
                    self.human_win_count[k] += 1
                    # AI在这个模式中不可能获胜了
                    self.ai_win_count[k] = 6

    def evaluate_position(self, human_score, ai_score):
        OFFENSIVE_WEIGHT = 1.2  # 进攻权重：鼓励AI积极进攻
        DEFENSIVE_WEIGHT = 1.0  # 防守权重：阻止玩家连成五子
        # 综合得分 = AI进攻得分 * 进攻权重 + 防守玩家得分 * 防守权重
        return ai_score * OFFENSIVE_WEIGHT + human_score * DEFENSIVE_WEIGHT

    def ai_run(self, board):
        # 初始化最佳位置和最佳得分
        best_pos = (0, 0)  # 最佳位置（默认左上角）
        best_score = -1    # 最佳得分（初始为-1）
        
        # 遍历棋盘上的所有位置
        for i in range(1, BOARD_SIZE):
            for j in range(1, BOARD_SIZE):
                # 如果这个位置是空的
                if board[i][j] == 0:
                    # 重置当前位置i,j得分
                    cur_human_score, cur_ai_score = 0, 0
                    
                    # 遍历所有获胜模式，计算这个位置的得分
                    for k in range(TOTAL_WIN_PATTERNS):
                        # 如果这个位置属于第k个获胜模式
                        if self.win_patterns[i][j][k]:
                            # 累加玩家在这个模式下的得分
                            cur_human_score += self.human_score_weights.get(
                                self.human_win_count[k], 0)
                            # 累加AI在这个模式下的得分
                            cur_ai_score += self.ai_score_weights.get(
                                self.ai_win_count[k], 0)
                    
                    # 计算综合得分
                    cur_score = self.evaluate_position(cur_human_score, cur_ai_score)
                    
                    # 如果当前得分更好，更新最佳位置
                    if cur_score >= best_score:
                        best_score = cur_score
                        best_pos = (i, j)
        
        # 返回最佳落子位置
        return best_pos

class GomokuGame:
    
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
        self.my_color = StoneColor.BLACK # 玩家棋子颜色
        self.competitor_color = StoneColor.WHITE  # 对手棋子颜色
        self.my_turn = False  # 是否轮到玩家下棋
        self.game_over = False

        self.ai = None
        self.judge = None

        self.draw_board() # 绘制初始棋盘
        try:
            self.game_mode = GameMode.NETWORK
            self.tcp = TCPClient(self.tcp_callback, self.switch_to_ai)
        except Exception as e:
            print(f"切换为本地 AI 对战:{e}")
            self.switch_to_ai()

    def switch_to_ai(self):
        if not self.ai:
            self.ai = AI()
        if not self.judge:
            self.judge = Judge()
        try:
            self.tcp.disconnect()
            self.tcp = None
        except Exception as e:
            print({e})

        self.game_mode = GameMode.LOCAL_AI
        self.my_turn = True  # 玩家先手
        self.my_color = StoneColor.BLACK  # 玩家执黑
        self.competitor_color = StoneColor.WHITE # AI 执白
        
        self.msg_queue.put(("MSG", "本地AI对战 - 你执黑先手"))
        print(f"switch to ai {self.game_mode}")

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
            self.tcp.is_matched = True
            print("游戏开始：", "你执黑先手" if x == 1 else "你执白后手")
            color_name = "黑棋(先手)" if x == 1 else "白棋(后手)"
            self.msg_queue.put(("MSG", f"匹配成功！你执{color_name}"))
            self.my_color = x  # 游戏开始，玩家执黑先手
            self.competitor_color = y  # 对手颜色
            if self.my_color == StoneColor.BLACK:
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
                        self.make_move(grid_x, grid_y, self.my_color)
            
            # 更新整个游戏窗口的显示
            pygame.display.update()

    def make_move(self, grid_x, grid_y, color):
        if self.game_over:
            return False
        if not (0 < grid_x < BOARD_SIZE and 0 < grid_y < BOARD_SIZE):
            return False
        if self.game_mode == GameMode.LOCAL_AI and self.judge.board[grid_x][grid_y] != 0:
            return False
        self.place_stone(grid_x, grid_y, color)
        if self.game_mode == GameMode.NETWORK:
            self.tcp.send_msg(Cmd.MSG_MAKE_MOVE, grid_x, grid_y)  # 向服务器发送落子消息
            if color == self.my_color:
                self.my_turn = False
                self.msg_queue.put(("MSG", f"对方回合，等待对手落子..."))
            return True
        else:
            # 更新棋盘状态，并检查是否获胜
            winner = self.judge.update_board(grid_x, grid_y, color)
            self.ai.update_win_counts(grid_x, grid_y, color)
            if winner:
                self.game_over = True  # 锁定游戏状态
                msg = "白方获胜" if winner == StoneColor.WHITE else "黑方获胜"
                self.msg_queue.put(("MSG", msg))
                self.my_turn = False
                return True
            if color == self.my_color:
                self.my_turn = False
                # 开启一个微延迟或者直接调用 AI
                self.handle_ai_turn()
                if not self.game_over:                    
                    self.msg_queue.put(("MSG", "轮到你下棋..."))

    def handle_ai_turn(self):
        # AI计算最佳落子位置
        ai_x, ai_y = self.ai.ai_run(self.judge.board)
        # 处理AI落子
        self.make_move(ai_x, ai_y, self.competitor_color)
        self.my_turn = True

    def place_stone(self, grid_x, grid_y, color):
        # 根据颜色选择棋子颜色
        stone_color = COLORS["black_stone"] if color == StoneColor.BLACK else COLORS["white_stone"]
        pygame.draw.circle(self.window, stone_color, (grid_x * GAP, grid_y * GAP), STONE_SIZE)
        pygame.display.update()
    
    def compute_grid_position(self, x, y):
        grid_x = round(x / GAP)
        grid_y = round(y / GAP)
        
        # 确保坐标在有效范围内（1到BOARD_SIZE-1）
        grid_x = max(1, min(BOARD_SIZE - 1, grid_x))
        grid_y = max(1, min(BOARD_SIZE - 1, grid_y))

        return grid_x, grid_y
    
    def draw_board(self):
        self.window.fill(COLORS["background"])
        
        for i in range(BOARD_SIZE):
            # 绘制水平线：从左到右
            pygame.draw.line(self.window, COLORS["line"],
                            (GAP, GAP * (i + 1)),
                            (WINDOW_SIZE - GAP, GAP * (i + 1)),
                            1)
            
            # 绘制垂直线：从上到下
            pygame.draw.line(self.window, COLORS["line"],
                            (GAP * (i + 1), GAP),
                            (GAP * (i + 1), WINDOW_SIZE - GAP),
                            1)
            
        # 绘制五个星位点（棋盘上的小黑点）
        for point in POINTS:
            pixel_x = GAP * (point[0] + 1)
            pixel_y = GAP * (point[1] + 1)
            
            pygame.draw.circle(self.window, COLORS["line"], 
                              (pixel_x, pixel_y), 5)

def main():
    game = GomokuGame()
    game.main_loop()

if __name__ == "__main__":
    main()