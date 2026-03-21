import pygame
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
    pass

class Platform:
    pass

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

    def update(self): # 更新游戏数据
        pass
    
    def draw(self): # 绘制游戏画面
        self.screen.blit(self.bg, (0, 0)) # 绘制背景图片

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