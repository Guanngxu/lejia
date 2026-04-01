import pygame
import random
import sys
import os


SCREEN_WIDTH, SCREEN_HEIGHT = 400, 600  # 定义游戏窗口的宽度和高度
FPS = 60                                # 每秒刷新的帧数，控制游戏运行流畅度
GRAVITY = 0.7                           # 模拟物理重力，每帧给玩家增加的向下速度


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

class Player:
    def __init__(self):
        self.image = Utils.load_img("player.png", (40, 40)) # 加载玩家图片并缩放到40x40像素
        # 第一个平台离 y 轴 50，平台高度 20，所以减去 70
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70)) # 获取玩家图片的矩形区域，用于碰撞检测和位置管理
        self.speed_y = 0 # 玩家在 y 轴上的速度，初始为0

    def update(self):
        self.speed_y += GRAVITY # 每帧增加重力加速度
        self.rect.y += self.speed_y # 根据速度更新玩家的 y 坐标

    def draw(self, screen):
        screen.blit(self.image, self.rect) # 将玩家图片绘制在屏幕底部中央位置

class Platform:
    def __init__(self, x, y):
        self.image = Utils.load_img("platform.png", (70, 20)) # 加载平台图片并缩放到70x20像素
        self.rect = self.image.get_rect(topleft=(x, y)) # 获取平台图片的矩形区域，用于碰撞检测和位置管理

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect) # 将平台图片绘制在屏幕上

class Item:
    pass

class Spring(Item):
    pass

class Propeller(Item):
    pass

class GameSession:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Doodle Jump By Guanngxu")
        self.clock = pygame.time.Clock()
        self.bg = Utils.load_img("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT)) # 加载背景图片
        self.player = Player() # 创建玩家实例
        self.platforms = []
        self._init_platforms() # 初始化平台列表

    def _init_platforms(self):
        # 在屏幕底部中央创建一个初始平台，确保玩家有地方跳
        # platform 的 width 为 70，所以 x 坐标需要减去 35 来居中
        platform = Platform(SCREEN_WIDTH // 2 - 35, SCREEN_HEIGHT - 50)
        self.platforms.append(platform)
        # 初始化一些平台，确保玩家有地方跳
        for i in range(8):
            platform = Platform(random.randint(0, SCREEN_WIDTH - 70), SCREEN_HEIGHT - (i * 80) - 150)
            self.platforms.append(platform)

    def update(self): # 更新游戏数据
        for platform in self.platforms:
            platform.update() # 更新平台状态
        self.player.update() # 更新玩家状态

        for platform in self.platforms:
            # 检测玩家是否与平台发生碰撞，并且玩家正在向下移动时检测，向上移动时不检测
            if self.player.rect.colliderect(platform.rect) and self.player.speed_y > 0:
                self.player.speed_y = -15 # 碰撞后给予玩家一个向上的速度，模拟跳跃效果
    
    def draw(self): # 绘制游戏画面
        self.screen.blit(self.bg, (0, 0)) # 绘制背景图片
        for platform in self.platforms:
            platform.draw(self.screen) # 绘制平台
        self.player.draw(self.screen) # 绘制玩家

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            self.update()
            self.draw()

            self.clock.tick(FPS)  # 控制游戏循环以每秒FPS帧的速度运行
            pygame.display.flip()  # 更新屏幕显示



if __name__ == "__main__":
    GameSession().run()