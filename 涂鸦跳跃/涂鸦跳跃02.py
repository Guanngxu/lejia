import pygame
import sys


SCREEN_WIDTH, SCREEN_HEIGHT = 400, 600  # 定义游戏窗口的宽度和高度
FPS = 60                                # 每秒刷新的帧数，控制游戏运行流畅度


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

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            self.clock.tick(FPS)  # 控制游戏循环以每秒FPS帧的速度运行
            self.screen.fill((255, 255, 255))  # 填充背景为白色
            pygame.display.flip()  # 更新屏幕显示


if __name__ == "__main__":
    GameSession().run()