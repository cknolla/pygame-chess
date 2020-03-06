#!/usr/bin/env python3
"""
https://realpython.com/pygame-a-primer/
"""
import random
import pickle

import pygame

from pygame.locals import (
    K_w,
    K_s,
    K_a,
    K_d,
    K_q,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640


class Board:
    def __init__(self):
        self.positions = [
            [BoardPosition(x, y) for x in range(8)] for y in range(8)
        ]
        # print(self.positions)


class BoardPosition:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.game_piece = None

    def __repr__(self):
        return f'<BoardPosition: {self.x}, {self.y}>'

    def __str__(self):
        return f'<BoardPosition: {chr(self.x + 97)}{self.y}'


class GamePiece:
    def __init__(self, image, board_position, player):
        self.image = image
        self.board_position = board_position
        self.player = player

    def move(self):
        raise NotImplementedError('Child class must define a movement')


def get_center(parent_surface: pygame.Surface, child_surface: pygame.Surface):
    return ((parent_surface.get_width() - child_surface.get_width()) / 2,
            (parent_surface.get_height() - child_surface.get_height()) / 2)


class GameSession:
    def __init__(self):
        self.playtime = 0.0


class Pygame:
    def __init__(self, width: int, height: int, fps: int = 60):
        """
        :param width:
        :param height:
        :param fps:
        """
        pygame.init()
        pygame.display.set_caption("Press ESC to quit")
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        self.screen.fill((255, 0, 255))
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.game_session: GameSession = self.load()
        self.font = pygame.font.SysFont('mono', 20, bold=True)
        self.all_sprites = pygame.sprite.Group()

        self.board = Board()

    def run(self):
        """
        Main event loop
        :return:
        """
        running = True
        while running:
            milliseconds = self.clock.tick(self.fps)
            self.game_session.playtime += milliseconds / 1000.0

            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key in [K_ESCAPE, K_q]):
                    running = False

            self.background.fill((255, 255, 255))

            for sprite in self.all_sprites:
                self.screen.blit(sprite.surf, sprite.rect)

            self.draw_text(
                f"Playtime: {self.game_session.playtime:.2f}")

            pygame.display.flip()
            self.screen.blit(self.background, (0, 0))

        pygame.quit()

    def load(self) -> GameSession:
        try:
            with open('data.dat', 'rb') as file:
                return pickle.load(file)
        except FileNotFoundError:
            return GameSession()

    def save(self):
        with open('data.dat', 'wb') as file:
            pickle.dump(self.game_session, file)

    def draw_text(self, text: str):
        """
        Draw text in window
        :param text:
        :return:
        """
        font_width, font_height = self.font.size(text)
        surface = self.font.render(text, True, (0, 255, 0))
        self.screen.blit(surface, (0, 0))


if __name__ == '__main__':
    Pygame(SCREEN_WIDTH, SCREEN_HEIGHT).run()
