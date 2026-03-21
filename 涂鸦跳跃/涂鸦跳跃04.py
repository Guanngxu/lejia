import pygame
import random
import sys
import os


SCREEN_WIDTH, SCREEN_HEIGHT = 400, 600  # 定义游戏窗口的宽度和高度
FPS = 60                                # 每秒刷新的帧数，控制游戏运行流畅度


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
        self.rect = self.image.get_rect() # 获取玩家图片的矩形区域，用于碰撞检测和位置管理

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect) # 将玩家图片绘制在屏幕底部中央位置

class Platform:
    def __init__(self):
        self.image = Utils.load_img("platform.png", (70, 20)) # 加载平台图片并缩放到70x20像素
        self.rect = self.image.get_rect() # 获取平台图片的矩形区域，用于碰撞检测和位置管理

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
        platform = Platform()
        platform.rect.x = SCREEN_WIDTH // 2 - platform.rect.width // 2
        platform.rect.y = SCREEN_HEIGHT - 50
        self.platforms.append(platform)
        # 初始化一些平台，确保玩家有地方跳
        for i in range(5):
            platform = Platform()
            platform.rect.x = random.randint(0, SCREEN_WIDTH - platform.rect.width)
            platform.rect.y = random.randint(0, SCREEN_HEIGHT - platform.rect.height)
            self.platforms.append(platform)


    def update(self): # 更新游戏数据
        pass
    
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