import pygame    # 导入pygame库，用于处理图形、声音和用户输入
import random    # 导入随机数库，用于生成随机的踏板位置和道具
import os        # 导入操作系统接口库，用于处理文件路径

# --- 游戏配置参数（全局常量） ---
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 600  # 定义游戏窗口的宽度和高度
FPS = 60                                # 每秒刷新的帧数，控制游戏运行流畅度
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (100, 100, 100) # 颜色常量（RGB）
TITLE_COLOR = (255, 120, 0)             # 主界面标题的颜色

GRAVITY = 0.7                           # 模拟物理重力，每帧给玩家增加的向下速度
JUMP_STRENGTH = -16                     # 玩家踩到普通踏板时获得的向上初速度（y轴负方向为上）
SUPER_JUMP_STRENGTH = -26               # 踩到弹簧时获得的超强跳跃力度
FLY_STRENGTH = -12                      # 使用竹蜻蜓时的持续上升推力
FLY_DURATION = 150                      # 竹蜻蜓效果持续的帧数（约2.5秒）

# --- 资源加载助手函数 ---
def load_img(name, scale=None):
    """
    功能：从本地磁盘加载图片并进行优化处理
    name: 文件名
    scale: 缩放尺寸 (width, height)
    """
    path = os.path.join("./images/", name) # 拼接图片路径
    try:
        img = pygame.image.load(path).convert_alpha() # 加载图片并转换Alpha通道（透明度优化）
        if scale: img = pygame.transform.scale(img, scale) # 如果指定了尺寸，则进行缩放
        return img
    except:
        # 如果图片丢失，生成一个占位用的灰色方块，确保程序不崩溃
        surf = pygame.Surface(scale if scale else (30, 30))
        surf.fill((200, 200, 200))
        return surf

def load_sound(name):
    """
    功能：尝试加载不同后缀名的音效文件
    """
    base_path = "./sounds/"
    for ext in ['.wav', '.mp3', '.ogg']: # 遍历常见的音频格式
        full_path = os.path.join(base_path, name + ext)
        if os.path.exists(full_path):
            try: return pygame.mixer.Sound(full_path)
            except: continue
    return None

# --- 道具基类（父类） ---
class Item:
    def __init__(self, platform):
        self.platform = platform    # 道具绑定的踏板对象
        self.frames = []            # 存放动画序列帧
        self.current_frame = 0      # 动画当前帧的索引
        self.anim_speed = 0.3       # 动画播放速度（每帧增加的索引值）
        self.is_active = False      # 标记道具是否已被触发
        self.image = None           # 当前要显示的图片对象
        self.rect = None            # 道具在屏幕上的矩形位置

    def update_pos(self):
        """让道具始终固定在踏板的中心顶部"""
        if self.platform:
            self.rect.midbottom = self.platform.rect.midtop

    def animate(self):
        """通用动画逻辑：循环切换图片帧"""
        if self.is_active and len(self.frames) > 1:
            self.current_frame += self.anim_speed
            if self.current_frame >= len(self.frames): 
                self.current_frame = 0
            self.image = self.frames[int(self.current_frame)]
        elif self.frames:
            self.image = self.frames[0] # 未激活时显示第一帧

    def draw(self, screen):
        """将道具绘制到屏幕上"""
        if self.image: screen.blit(self.image, self.rect)

# --- 弹簧类（继承自Item） ---
class Spring(Item):
    def __init__(self, platform, sound):
        super().__init__(platform) # 调用父类初始化
        self.sound = sound
        # 弹簧有两个状态图片：压缩(0)和拉伸(1)
        self.frames = [load_img("spring_0.png", (25, 20)), load_img("spring_1.png", (25, 30))]
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.update_pos()

    def apply_effect(self, player):
        """触发效果：瞬间给予玩家极大的向上速度"""
        if not self.is_active:
            self.is_active = True
            if self.sound: self.sound.play()
            player.rect.bottom = self.rect.top # 修正玩家位置到弹簧顶部
            player.jump(SUPER_JUMP_STRENGTH, play_sound=False) # 执行大跳
            return True
        return False

    def animate(self):
        """重写弹簧动画：激活后停留在拉伸状态，不循环"""
        if self.is_active:
            if self.current_frame < len(self.frames) - 1:
                self.current_frame += self.anim_speed
            self.image = self.frames[int(self.current_frame)]
        else:
            self.image = self.frames[0]

# --- 竹蜻蜓类（继承自Item） ---
class Propeller(Item):
    def __init__(self, platform, sound):
        super().__init__(platform)
        self.sound = sound
        # 加载扇叶旋转的两个画面
        self.frames = [load_img("propeller_0.png", (40, 20)), load_img("propeller_1.png", (40, 20))]
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.update_pos()

    def apply_effect(self, player):
        """触发效果：开启飞行计时器，并把自己挂在玩家头顶"""
        if not self.is_active:
            self.is_active = True
            if self.sound: self.sound.play()
            player.fly_timer = FLY_DURATION # 设置飞行剩余帧数
            player.active_item = self       # 建立关联，让玩家带动道具移动
            return True
        return False

# --- 角色类 ---
class Player:
    def __init__(self, jump_sound):
        self.image = load_img("player.png", (40, 40)) # 加载玩家图片
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        self.vel_y = 0              # 当前y轴垂直速度
        self.speed = 8              # 左右移动的水平速度
        self.fly_timer = 0          # 飞行状态计时器
        self.active_item = None     # 当前持有的特殊道具（如竹蜻蜓）
        self.jump_sound = jump_sound

    def update(self):
        # 飞行逻辑：计时器大于0时，无视重力，强制向上移动
        if self.fly_timer > 0:
            self.fly_timer -= 1
            self.vel_y = FLY_STRENGTH
            if self.active_item:
                self.active_item.animate()  # 更新扇叶旋转动画
                self.active_item.rect.midbottom = self.rect.midtop # 让竹蜻蜓贴合头部
                self.active_item.rect.centery -= 5 # 细节微调位置
                self.active_item.rect.centerx -= 5
            if self.fly_timer == 0: self.active_item = None # 飞行结束，道具失效
        else:
            # 普通逻辑：模拟物理重力，每帧增加向下的速度分量
            self.vel_y += GRAVITY
        
        self.rect.y += self.vel_y # 根据速度更新坐标
        
        # 处理左右键盘输入
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed
        
        # 屏幕边缘穿梭（Pac-man风格）：从左边缘消失从右边出现
        if self.rect.right < 0: self.rect.left = SCREEN_WIDTH
        elif self.rect.left > SCREEN_WIDTH: self.rect.right = 0

    def jump(self, force=JUMP_STRENGTH, play_sound=True):
        """执行跳跃：给y轴设置负向初速度"""
        self.vel_y = force
        if play_sound and self.jump_sound and self.fly_timer <= 0:
            self.jump_sound.play()

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        if self.active_item: self.active_item.draw(screen) # 如果有竹蜻蜓，一并画出来

# --- 踏板类 ---
class Platform:
    def __init__(self, x, y):
        self.image = load_img("platform.png", (70, 18))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.item = None # 踏板上可能挂载的道具对象

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        if self.item:
            self.item.update_pos() # 先同步道具坐标
            self.item.draw(screen)  # 再绘制道具

# --- 云朵背景类 ---
class Cloud:
    def __init__(self):
        # 随机缩放云朵，增加多样性
        size = random.randint(60, 120)
        self.image = load_img("cloud.png", (size, int(size * 0.6)))
        # 随机初始位置
        self.rect = self.image.get_rect(
            x=random.randint(0, SCREEN_WIDTH),
            y=random.randint(0, SCREEN_HEIGHT)
        )
        # 随机漂移速度 (0.2 到 0.8 像素每帧)
        self.speed = random.uniform(0.2, 0.8)
        # 随机方向 (-1 向左, 1 向右)
        self.direction = random.choice([-1, 1])

    def update(self, scroll_amt):
        # 1. 随背景滚动
        self.rect.y += scroll_amt * 0.5  # 云朵滚动比踏板慢，产生视差效果
        
        # 2. 水平自动漂移
        self.rect.x += self.speed * self.direction
        
        # 3. 边缘处理
        if self.rect.left > SCREEN_WIDTH: self.rect.right = 0
        elif self.rect.right < 0: self.rect.left = SCREEN_WIDTH
        
        # 4. 垂直循环：如果云朵掉出底部，重置到顶部上方
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.y = random.randint(-150, -50)
            self.rect.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, screen):
        # 设置一点透明度（如果你的pygame版本支持）
        screen.blit(self.image, self.rect)

# --- 游戏核心世界逻辑 ---
class GameWorld:
    def __init__(self, snd_jump, snd_spring, snd_propeller, item_probs):
        self.bg = load_img("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.snd_jump, self.snd_spring, self.snd_propeller = snd_jump, snd_spring, snd_propeller
        self.item_probs = item_probs # 道具生成概率字典
        self.player = Player(snd_jump)
        self.platforms = []          # 存储当前屏幕内所有踏板
        self.score = 0               # 游戏得分
        self.font = pygame.font.SysFont("Arial", 28, bold=True)
        self.clouds = [Cloud() for _ in range(5)]  # 初始化5朵云
        self._init_level()           # 初始化首批踏板

    def _init_level(self):
        """初始布局：保证玩家出生脚下有一个踏板，并在上方均匀分布几个踏板"""
        self.platforms.append(Platform(SCREEN_WIDTH//2-35, SCREEN_HEIGHT-50))
        for i in range(8): self._spawn_platform(SCREEN_HEIGHT - (i * 80) - 150)

    def _spawn_platform(self, y):
        """在指定高度 y 随机生成一个踏板，并防止重叠"""
        attempts = 0
        while attempts < 15: # 最多尝试15次，防止死循环
            x = random.randint(0, SCREEN_WIDTH - 70)
            # 碰撞检查：新踏板不能离旧踏板太近
            is_overlap = any(abs(x - p.rect.x) < 85 and abs(y - p.rect.y) < 30 for p in self.platforms)
            if not is_overlap: break
            attempts += 1
        
        p = Platform(x, y)
        # 根据概率随机生成道具
        r = random.random()
        if r < self.item_probs['spring']: 
            p.item = Spring(p, self.snd_spring)
        elif r < self.item_probs['spring'] + self.item_probs['propeller']:
            p.item = Propeller(p, self.snd_propeller)
        self.platforms.append(p)

    def update(self):
        """核心逻辑更新"""
        # 1. 屏幕滚动：当玩家跳过屏幕 1/3 高度时，背景整体向下滚动
        scroll_amt = 0
        if self.player.rect.y <= SCREEN_HEIGHT // 3 and self.player.vel_y < 0:
            scroll_amt = -self.player.vel_y # 滚动的距离等于玩家向上冲的距离
            self.player.rect.y = SCREEN_HEIGHT // 3 # 玩家视觉上保持在1/3处不动

        # 2. 更新云朵位置
        for c in self.clouds:
            c.update(scroll_amt)

        # 3. 移动所有踏板位置
        for p in self.platforms: 
            p.rect.y += scroll_amt
            if p.item: p.item.animate() # 顺便更新道具动画

        self.player.update() # 更新玩家物理状态

        keys = pygame.key.get_pressed()
        # 4. 碰撞检测：只有当玩家向下掉落时才触发踩踏板逻辑
        if self.player.vel_y >= 0:
            for p in self.platforms:
                # 检查是否碰到道具
                if p.item and self.player.rect.colliderect(p.item.rect):
                    if not p.item.is_active:
                        if isinstance(p.item, Spring):
                            p.item.apply_effect(self.player)
                            continue # 触发弹簧后跳过普通踏板判断
                        elif isinstance(p.item, Propeller):
                            if p.item.apply_effect(self.player):
                                p.item = None # 捡走竹蜻蜓，从踏板移除
                                continue

                # 检查是否落到踏板上
                if self.player.rect.colliderect(p.rect):
                    # 碰撞阈值判定：确保是从上往下踩，而非从侧面或底部撞
                    if p.rect.top < self.player.rect.bottom < p.rect.bottom + 15:
                        self.player.rect.bottom = p.rect.top
                        self.player.vel_y = 0 # 站稳
                        if keys[pygame.K_SPACE]: # 只有按空格才跳跃（如果你想改成自动跳，可以移除这里的if）
                            self.player.jump()
                        break

        # 5. 回收与生成：移除掉出屏幕底部的踏板，并在顶部生成新踏板
        for p in self.platforms[:]:
            if p.rect.y > SCREEN_HEIGHT:
                self.platforms.remove(p)
                self._spawn_platform(random.randint(-70, -30))
                self.score += 1 # 踩过（或滑过）一个踏板得1分

    def draw(self, screen):
        """绘制游戏内所有元素"""
        screen.blit(self.bg, (0, 0)) # 画背景
        for c in self.clouds: c.draw(screen) # 画云朵
        for p in self.platforms: p.draw(screen) # 画踏板和道具
        self.player.draw(screen) # 画玩家
        # 绘制实时分数
        score_txt = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_txt, (20, 20))

# --- 游戏控制器（状态机） ---
class GameController:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        # 加载所有声音
        self.snd_jump = load_sound("jump")
        self.snd_spring = load_sound("spring")
        self.snd_propeller = load_sound("propeller")
        
        self.bg = load_img("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.probs = {'spring': 0.05, 'propeller': 0.02} # 设置道具出现的几率
        self.state = "MENU" # 状态机标志：MENU(菜单) 或 PLAYING(游戏中)
        
        # 预设不同用途的字体
        self.title_font = pygame.font.SysFont("Comic Sans MS", 55, bold=True)
        self.author_font = pygame.font.SysFont("Arial", 22, italic=True)
        self.start_font = pygame.font.SysFont("Arial", 26, bold=True)

    def draw_menu(self):
        """绘制主菜单画面"""
        self.screen.blit(self.bg, (0, 0))
        # 渲染标题
        title_surf = self.title_font.render("Doodle Jump", True, TITLE_COLOR)
        self.screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 120))
        # 渲染作者信息
        author_surf = self.author_font.render("Author: Guanngxu", True, BLACK)
        self.screen.blit(author_surf, (SCREEN_WIDTH//2 - author_surf.get_width()//2, 210))
        # 渲染提示文字
        msg = self.start_font.render("Press [ SPACE ] to Start", True, (50, 50, 50))
        self.screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, 380))
        pygame.display.flip()

    def run(self):
        """游戏主循环引擎"""
        while True:
            # --- 菜单状态 ---
            if self.state == "MENU":
                self.draw_menu()
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: return # 退出程序
                    if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                        # 按空格键：重置游戏世界并开始
                        self.world = GameWorld(self.snd_jump, self.snd_spring, self.snd_propeller, self.probs)
                        self.state = "PLAYING"
            
            # --- 游戏进行状态 ---
            elif self.state == "PLAYING":
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: return
                
                self.world.update() # 更新世界逻辑
                
                # 死亡判定：如果玩家掉落到底部以下
                if self.world.player.rect.top > SCREEN_HEIGHT: 
                    self.state = "MENU" # 返回菜单
                
                self.world.draw(self.screen) # 渲染画面
                pygame.display.flip()        # 刷新屏幕显示
                self.clock.tick(FPS)         # 锁定帧率

# --- 程序入口 ---
if __name__ == "__main__":
    # 初始化混音器（增加缓冲区参数以降低声音延迟）
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Doodle Jump By Guanngxu")
    
    # 创建控制器并运行
    GameController(screen).run()
    
    pygame.quit() # 安全退出