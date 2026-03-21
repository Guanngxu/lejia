import pygame
import random
import sys
import os


SCREEN_WIDTH, SCREEN_HEIGHT = 400, 600  # 定义游戏窗口的宽度和高度
FPS = 60                                # 每秒刷新的帧数，控制游戏运行流畅度
GRAVITY = 0.7                           # 模拟物理重力，每帧给玩家增加的向下速度
SPRING_JUMP_VELOCITY = -20              # 弹簧给予玩家的跳跃速度，经验值，表示比普通跳跃更高的跳跃效果
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (100, 100, 100) # 颜色常量（RGB）
TITLE_COLOR = (255, 120, 0)             # 主界面标题的颜色

class Utils:
    # --- 资源加载助手函数 ---
    @staticmethod
    def load_img(name, scale=None):
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
    
    @staticmethod
    def load_sound(name):
        base_path = "./sounds/"
        for ext in ['.wav', '.mp3', '.ogg']: # 遍历常见的音频格式
            full_path = os.path.join(base_path, name + ext)
            if os.path.exists(full_path):
                try: return pygame.mixer.Sound(full_path)
                except: continue
        return None # 如果没有找到任何格式的音效文件，返回 None

    @staticmethod
    def hit_probability(prob):
        return random.random() < prob # 返回一个布尔值，表示是否以给定概率命中

class Player:
    def __init__(self):
        self.image = Utils.load_img("player.png", (40, 40)) # 加载玩家图片并缩放到40x40像素
        # 第一个平台离 y 轴 50，平台高度 20，所以减去 70
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70)) # 获取玩家图片的矩形区域，用于碰撞检测和位置管理
        self.speed_y = 0 # 玩家在 y 轴上的速度，初始为0
        self.speed_x = 8 # 玩家在 x 轴上的速度，固定为8
        self.jump_sound = Utils.load_sound("jump") # 加载跳跃音效
        self.active_item = None # 记录当前正在影响玩家的道具实例，方便在 update 中处理道具效果

    def jump(self):
        self.speed_y = -15 # 碰撞后给予玩家一个向上的速度，模拟跳跃效果
        if self.jump_sound:
            self.jump_sound.play() # 播放跳跃音效

    def update(self):
        if self.active_item:
            self.active_item.update() # 如果有正在影响玩家的道具，更新道具状态，处理道具效果
            self.active_item.animate() # 如果有正在影响玩家的道具，执行道具动画
            self.active_item.follow_player(self) # 如果有正在影响玩家的道具，执行跟随玩家的逻辑，保持道具与玩家位置同步
            self.speed_y = self.active_item.fly_velocity - GRAVITY # 竹蜻蜓效果期间，玩家获得一个持续的向上的速度，模拟竹蜻蜓效果
            if self.active_item.fly_duration_timer <= 0: # 竹蜻蜓效果结束
                self.active_item = None # 重置当前正在影响玩家的道具实例，结束竹蜻蜓效果

        self.speed_y += GRAVITY # 每帧增加重力加速度
        self.rect.y += self.speed_y # 根据速度更新玩家的 y 坐标
        
        # 处理键盘左右键输入
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed_x # 向左移动
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed_x # 向右移动

        if self.rect.right < 0: # 如果玩家完全移出左边界
            self.rect.left = SCREEN_WIDTH # 从右边重新出现
        elif self.rect.left > SCREEN_WIDTH: # 如果玩家完全移出右边界
            self.rect.right = 0 # 从左边重新出现

    def draw(self, screen):
        screen.blit(self.image, self.rect) # 将玩家图片绘制在屏幕底部中央位置
        if self.active_item:
            self.active_item.draw(screen) # 如果有正在影响玩家的道具，绘制道具

class Platform:
    def __init__(self, x, y):
        self.image = Utils.load_img("platform.png", (70, 20)) # 加载平台图片并缩放到70x20像素
        self.rect = self.image.get_rect(topleft=(x, y)) # 获取平台图片的矩形区域，用于碰撞检测和位置管理
        self.item = None # 平台上可能有一个道具，初始为 None

    def update(self):
        if self.item:
            self.item.update() # 如果平台上有道具，更新道具状态
            self.item.animate() # 如果平台上有道具，执行道具动画

    def draw(self, screen):
        screen.blit(self.image, self.rect) # 将平台图片绘制在屏幕上
        if self.item:
            self.item.draw(screen) # 如果平台上有道具，绘制道具

class Item:
    probability = 0.3 # 物品生成的概率，默认30%
    animate_speed = 0.2 # 物品动画的速度，经验值，表示每帧切换动画的概率
    
    def __init__(self, platform):
        self.platform = platform # 物品所在的平台
        self.frames = [] # 存储动画帧的列表
        self.current_frame_index = 0 # 当前动画帧的索引
        self.animate_timer = 0 # 动画计时器，用于控制动画切换速度
        self.rect = None # 物品的矩形区域，用于碰撞检测和位置管理
        self.has_used = False # 物品是否已经被玩家使用过，避免重复使用

    # 某些道具需要跟随玩家移动，比如竹蜻蜓，这个方法可以用来实现跟随玩家的逻辑
    def follow_player(self, player):
        pass

    def apply_effect(self, player):
        pass

    def animate(self):
        pass
    
    def update(self):
        self.rect.midbottom = self.platform.rect.midtop # 物品始终跟随平台移动，保持在平台顶部

    def draw(self, screen):
        if self.frames:
            screen.blit(self.frames[self.current_frame_index], self.rect) # 绘制当前动画帧

class Spring(Item):
    probability = 0.2 # 弹簧生成的概率，20%

    def __init__(self, platform):
        super().__init__(platform)
        self.frames = [Utils.load_img(f"spring_{i}.png", (30, 30)) for i in range(2)] # 加载弹簧的两帧动画
        self.rect = self.frames[0].get_rect() # 获取弹簧图片的矩形区域，用于碰撞检测和位置管理
        self.sound = Utils.load_sound("spring") # 加载弹簧音效
        self.animate_played = False # 标记动画是否已经播放过，避免重复播放

    def apply_effect(self, player):
        if self.has_used: return # 如果已经被使用过，直接返回，避免重复使用
        self.has_used = True # 标记为已使用
        player.speed_y = SPRING_JUMP_VELOCITY # 弹簧给予玩家一个更强的向上的速度，模拟更高的跳跃效果
        if self.sound:
            self.sound.play() # 播放弹簧音效
    
    def animate(self):
        if self.has_used and not self.animate_played:
            self.animate_timer += self.animate_speed # 增加动画计时器
            if self.animate_timer >= 1: # 如果计时器达到切换动画的条件
                self.animate_timer = 0 # 重置动画计时器
                self.current_frame_index = (self.current_frame_index + 1) % len(self.frames) # 切换到下一帧动画
                if self.current_frame_index == len(self.frames) - 1: # 如果动画已经播放到最后一帧，标记动画已经播放过
                    self.animate_played = True
        elif not self.has_used:
            self.current_frame_index = 0 # 如果没有被使用过，保持在第一帧动画

class Propeller(Item):
    probability = 0.1 # 螺旋桨生成的概率，10%
    animate_speed = 0.1 # 螺旋桨动画的速度，经验值，表示每帧切换动画的概率
    def __init__(self, platform):
        super().__init__(platform)
        self.frames = [Utils.load_img(f"propeller_{i}.png", (40, 20)) for i in range(2)] # 加载螺旋桨的两帧动画
        self.rect = self.frames[0].get_rect() # 获取螺旋桨图片的矩形区域，用于碰撞检测和位置管理
        self.sound = Utils.load_sound("propeller") # 加载螺旋桨音效
        self.fly_duration_timer = 150 # 竹蜻蜓效果持续的帧数（约2.5秒）
        self.fly_velocity = -12 # 竹蜻蜓给予玩家的持续向上的速度，经验值，表示比普通跳跃更高的跳跃效果

    def follow_player(self, player):
        self.rect.midbottom = player.rect.midtop # 竹蜻蜓效果期间，物品跟随玩家移动，保持在玩家头顶
        self.rect.centerx -= 5 # 细节微调位置，让它更居中一些
        self.rect.centery -= 5

    def update(self):
        if not self.has_used:
            super().update() # 调用父类的 update 方法，保持物品跟随平台移动
        else:
            if self.has_used and self.fly_duration_timer > 0:
                self.fly_duration_timer -= 1 # 竹蜻蜓效果持续期间，减少计时器

    def apply_effect(self, player):
        if self.has_used: return # 如果已经被使用过，直接返回，避免重复使用
        self.platform.item = None # 使用后将平台上的道具引用清除，避免重复使用
        self.has_used = True # 标记为已使用
        player.active_item = self # 记录当前正在影响玩家的道具实例，方便在 update 中处理道具效果
        if self.sound:
            self.sound.play() # 播放螺旋桨音效
    
    def animate(self):
        if self.has_used:
            self.animate_timer += self.animate_speed # 增加动画计时器
            if self.animate_timer >= 1: # 如果计时器达到切换动画的条件
                self.animate_timer = 0 # 重置动画计时器
                self.current_frame_index = (self.current_frame_index + 1) % len(self.frames) # 切换到下一帧动画

class Cloud():
    def __init__(self):
        size = random.randint(50, 100) # 云朵的随机大小
        self.frame = Utils.load_img("cloud.png", (size, size // 2)) # 加载云朵图片并缩放到随机大小
        self.rect = self.frame.get_rect(
            x=random.randint(0, SCREEN_WIDTH - size), # 云朵的随机水平位置
            y=random.randint(0, SCREEN_HEIGHT // 2) # 云朵的随机垂直位置，限制在屏幕上半部分
        )
        self.direction = random.choice([-1, 1]) # 云朵的移动方向，-1表示向左，1表示向右
        self.speed = random.uniform(0.5, 1.5) # 云朵的移动速度，随机生成一个经验值
        self.alpha = random.randint(100, 255) # 云朵的随机透明度，增加视觉层次感

    def update(self):
        self.rect.x += self.direction * self.speed # 云朵以固定速度向左右移动
        if self.rect.right < 0: # 如果云朵完全移出左边界
            self.rect.left = SCREEN_WIDTH # 从右边重新出现
        elif self.rect.left > SCREEN_WIDTH: # 如果云朵完全移出右边界
            self.rect.right = 0 # 从左边重新出现
        
        if self.rect.top > SCREEN_HEIGHT: # 限制云朵在屏幕上半部分
            self.rect.y = random.randint(0, SCREEN_HEIGHT // 2) # 如果云朵漂浮到下半部分，随机重置到上半部分

    def draw(self, screen):
        # 设置透明度
        temp_surface = self.frame.copy()
        temp_surface.set_alpha(self.alpha)
        screen.blit(temp_surface, self.rect) # 绘制云朵图片

class GameSession:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Doodle Jump By Guanngxu")
        self.clock = pygame.time.Clock()
        self.bg = Utils.load_img("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT)) # 加载背景图片
        self.player = Player() # 创建玩家实例
        self.platforms = [] # 初始化平台列表
        self.clouds = [Cloud() for _ in range(5)] # 初始化云朵列表，创建5朵云
        self.score = 0 # 初始化分数
        self.score_font = pygame.font.SysFont("Arial", 24, bold=True) # 初始化字体对象，用于绘制分数
        self.title_font = pygame.font.SysFont("Comic Sans MS", 55, bold=True)
        self.author_font = pygame.font.SysFont("Arial", 22, italic=True)
        self.start_font = pygame.font.SysFont("Arial", 26, bold=True)
        self.state = "menu" # 游戏状态，初始为菜单界面
        self._init_platforms() # 初始化平台列表

    def _init_platforms(self):
        # 在屏幕底部中央创建一个初始平台，确保玩家有地方跳
        # platform 的 width 为 70，所以 x 坐标需要减去 35 来居中
        platform = Platform(SCREEN_WIDTH // 2 - 35, SCREEN_HEIGHT - 50)
        self.platforms.append(platform)
        # 初始化一些平台，确保玩家有地方跳
        # 初始化的平台没有道具
        for i in range(8):
            platform = Platform(random.randint(0, SCREEN_WIDTH - 70), SCREEN_HEIGHT - (i * 80) - 150)
            self.platforms.append(platform)

    def update_scroll(self):
        scroll_threshold = SCREEN_HEIGHT // 2 # 定义一个滚动阈值，当玩家超过这个高度时，平台开始向下滚动
        scroll_amount = 0 # 初始化滚动量
        if self.player.rect.top < scroll_threshold:
            scroll_amount = scroll_threshold - self.player.rect.top # 计算需要滚动的距离
            self.player.rect.top = scroll_threshold # 将玩家位置固定在滚动阈值上
            for platform in self.platforms:
                platform.rect.y += scroll_amount # 平台向下滚动

        # 平台向下滚动后，移除那些已经完全移出屏幕底部的平台，并在顶部生成新的平台
        self.platforms = [p for p in self.platforms if p.rect.top < SCREEN_HEIGHT]
        self.score += scroll_amount // 10 # 根据滚动距离增加分数，10 是一个经验值，表示每滚动10像素得1分
        while len(self.platforms) < 8: # 保持屏幕上至少有8个平台
            new_platform = Platform(random.randint(0, SCREEN_WIDTH - 70), random.randint(-100, -40))
            if Utils.hit_probability(Spring.probability): # 根据弹簧的生成概率决定是否在新平台上生成弹簧
                spring = Spring(new_platform)
                new_platform.item = spring # 将弹簧作为平台的一个属性，方便后续碰撞检测和更新
            elif Utils.hit_probability(Propeller.probability): # 根据螺旋桨的生成概率决定是否在新平台上生成螺旋桨
                propeller = Propeller(new_platform)
                new_platform.item = propeller # 将螺旋桨作为平台的一个属性，方便后续碰撞检测和更新
            self.platforms.append(new_platform)

        for cloud in self.clouds:
            cloud.rect.y += scroll_amount // 2 # 云朵以较慢的速度向下滚动，制造出远近层次感

    # 检测玩家与道具的碰撞，并处理道具效果
    def item_colliderect(self, item):
        # 检测玩家是否与道具发生碰撞，并且道具没有被使用过
        if self.player.rect.colliderect(item.rect) and not item.has_used:
            item.apply_effect(self.player) # 调用 apply_effect 方法

    # 检测玩家与平台的碰撞，并处理跳跃逻辑
    def platform_colliderect(self, platform):
        # 检测玩家是否与平台发生碰撞，并且玩家正在向下移动时检测，向上移动时不检测
        if self.player.rect.colliderect(platform.rect) and self.player.speed_y > 0:
            # 15 是一个经验值，表示玩家底部与平台顶部的碰撞距离，如果小于这个值才算真正的站在平台上，避免侧面碰撞误判
            if self.player.rect.bottom - platform.rect.top < 15: # 碰撞时只检测玩家底部与平台顶部的碰撞，避免侧面碰撞误判
                self.player.rect.bottom = platform.rect.top # 碰撞后将玩家的底部位置调整到平台的顶部，避免玩家穿过平台
                self.player.speed_y = 0 # 碰撞后将玩家的垂直速度重置为0，模拟站在平台上的效果
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]: # 只有按空格才跳跃
                    self.player.jump() # 调用玩家的 jump 方法，执行跳跃逻辑
                return True # 碰撞后返回 True，表示玩家成功站在平台上

    def reset_game(self):
        # 重新初始化游戏内的对象数据
        self.player = Player() 
        self.platforms = [] 
        self.clouds = [Cloud() for _ in range(5)] 
        self.score = 0
        self.state = "menu" # 回到菜单界面
        self._init_platforms() 

    def update(self): # 更新游戏数据
        self.update_scroll() # 更新滚动逻辑

        for cloud in self.clouds:
            cloud.update() # 更新云朵状态

        for platform in self.platforms:
            platform.update() # 更新平台状态
        self.player.update() # 更新玩家状态

        if self.player.speed_y >= 0: # 只有当玩家正在向下移动时才检测碰撞，向上移动时不检测
            # 检测玩家与平台的碰撞，并处理跳跃逻辑，同时检测玩家与道具的碰撞，并处理道具效果
            for platform in self.platforms:
                if platform.item: # 如果平台上有道具，检测玩家与道具的碰撞，并处理道具效果
                    self.item_colliderect(platform.item)
                if self.platform_colliderect(platform): # 检测玩家与平台的碰撞，并处理跳跃逻辑
                    break # 如果已经检测到玩家与一个平台发生碰撞并处理了跳跃逻辑，就不再继续检测其他平台，避免多重碰撞导致的跳跃问题
        
        if self.player.rect.top > SCREEN_HEIGHT: # 如果玩家掉出屏幕底部，游戏结束，重置游戏状态
            self.reset_game() # 重新初始化游戏状态，回到菜单界面

    def draw(self): # 绘制游戏画面
        self.screen.blit(self.bg, (0, 0)) # 绘制背景图片
        for cloud in self.clouds:
            cloud.draw(self.screen) # 绘制云朵
        for platform in self.platforms:
            platform.draw(self.screen) # 绘制平台
        self.player.draw(self.screen) # 绘制玩家
        scrore_text = self.score_font.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(scrore_text, (10, 10)) # 在屏幕左

    def draw_menu(self):
        self.screen.blit(self.bg, (0, 0)) # 绘制背景图片
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
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            if self.state == "menu":
                self.draw_menu()
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]: # 在菜单界面按空格开始游戏
                    self.state = "playing"
            elif self.state == "playing":
                self.update()
                self.draw()

            self.clock.tick(FPS)  # 控制游戏循环以每秒FPS帧的速度运行
            pygame.display.flip()  # 更新屏幕显示


if __name__ == "__main__":
    GameSession().run()