#!/usr/bin/env python3
"""
https://realpython.com/pygame-a-primer/
"""
import pickle
import json
import typing
from itertools import cycle
from enum import IntEnum

import pygame

from pygame.locals import (
    K_w,
    K_s,
    K_a,
    K_d,
    K_q,
    K_ESCAPE,
    KEYDOWN,
    MOUSEBUTTONDOWN,
    QUIT,
)

from spritesheet import SpriteSheet

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


class Player:
    def __init__(self, color: str, y_direction: int):
        self.color = color
        self.y_direction = y_direction
        self.pieces: typing.List[Piece] = []


class Board:
    def __init__(self):
        with open('board.json') as board_config_file:
            self.config = json.load(board_config_file)
        self.position_size = self.config.get('Size')
        self.rect = pygame.Rect(0, 0, self.position_size * 8, self.position_size * 8)
        self.rect.left = (SCREEN_WIDTH - self.rect.width) / 2
        self.rect.top = (SCREEN_HEIGHT - self.rect.height) / 2
        self.positions = [
            [Position(x, y, self) for y in range(8)] for x in range(8)
        ]
        # print(self.positions)


class Position(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, board: Board):
        super().__init__()
        self.x = x
        self.y = y
        self.board: Board = board
        self.piece: Piece = None
        self.surface = pygame.Surface((board.position_size, board.position_size))
        dark_config = board.config.get('Dark')
        light_config = board.config.get('Light')
        if (self.x % 2 == 0 and self.y % 2 == 0) or (self.x % 2 == 1 and self.y % 2 == 1):
            self.surface.fill((dark_config.get('R'), dark_config.get('G'), dark_config.get('B')))
        else:
            self.surface.fill((light_config.get('R'), light_config.get('G'), light_config.get('B')))
        self.rect: pygame.Rect = self.surface.get_rect()
        self.rect.left = board.rect.left + (self.x * self.surface.get_width())
        self.rect.bottom = board.rect.bottom - (self.y * self.surface.get_height())

    def __repr__(self):
        return f'<BoardPosition: {self.x}, {self.y}>'

    def __str__(self):
        return f'<BoardPosition: {chr(self.x + 97)}{self.y + 1}>'

    def update(self):
        """
        Sprite builtin update method
        :return:
        """

    def clear_piece(self):
        self.piece = None




class Piece(pygame.sprite.Sprite):
    def __init__(self, player: Player):
        super().__init__()
        self.name = self.__class__.__name__
        self.surface: pygame.Surface = None
        self.image: pygame.image = None
        self.rect: pygame.Rect = None
        # self.image = pygame.image.load(image)
        self.position: Position = None
        self.initial_position: Position = None
        self.player: Player = player
        player.pieces.append(self)
        # self.surface: pygame.Surface = pygame.image.load(image).convert()
        # self.rect = self.surface.get_rect()
        # self.player = player

    def set_image(self, filename: str):
        self.image = pygame.image.load(filename).convert_alpha()
        self.surface = self.image
        self.rect = self.image.get_rect()

    def set_position(self, position: Position):
        if self.position is None:
            self.initial_position = position
        else:
            # unset old position's piece
            self.position.piece = None
        self.position = position
        # reset position's piece to self
        position.piece = self
        self.rect.left = position.rect.left
        self.rect.top = position.rect.top

    def same_position(self, position: Position) -> bool:
        if position == self.position:
            print('Can\'t move to same position')
            return True
        return False

    def own_piece_interfering(self, position: Position) -> bool:
        if position.piece is not None and position.piece.player == self.player:
            print(f'Own {position.piece.name} in the way at destination')
            return True
        return False

    def straight_clear(self, position: Position) -> bool:
        board = position.board
        if position.x == self.position.x and position.y != self.position.y:
            for y in range(min(position.y, self.position.y), max(position.y, self.position.y), 1):
                if y == self.position.y:
                    continue
                if board.positions[position.x][y].piece is not None:
                    print(f'{board.positions[position.x][y]} has piece {board.positions[position.x][y].piece.name}')
                    return False
            return True
        if position.x != self.position.x and position.y == self.position.y:
            for x in range(min(position.x, self.position.x), max(position.x, self.position.x), 1):
                if x == self.position.x or x == position.x:
                    continue
                if board.positions[x][position.y].piece is not None:
                    print(f'{board.positions[x][position.y]} has piece {board.positions[x][position.y].piece.name}')
                    return False
            return True

    def diagonal_clear(self, position: Position) -> bool:
        board = position.board
        print(f'start position: {self.position.x},{self.position.y}, end position: {position.x},{position.y}')
        x_dif = position.x - self.position.x
        y_dif = position.y - self.position.y
        if abs(x_dif) == abs(y_dif):
            for dif in range(1, abs(x_dif), 1):
                x = self.position.x + (dif % x_dif) if x_dif > 0 else self.position.x - (dif % abs(x_dif))
                y = self.position.y + (dif % y_dif) if y_dif > 0 else self.position.y - (dif % abs(y_dif))
                # print(f'dif: {dif}, x: {x}, y: {y}')
                if board.positions[x][y].piece is not None:
                    print(
                        f'{board.positions[x][y]} has piece {board.positions[x][y].piece.name}')
                    return False
            return True

    # def draw(self):
    #     self.rect = self.image.get_rect()
    #     self.rect.topleft = 0, 0

    def can_move(self, position: Position) -> bool:
        raise NotImplementedError('Child class must define a movement')


class Pawn(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self.same_position(position):
            return False
        # own piece in the way
        elif self.own_piece_interfering(position):
            return False
        # standard forward move
        elif position.x == self.position.x and \
            position.y == (self.position.y + self.player.y_direction) and \
            position.piece is None:
            return True
        # double-move from starting position
        elif position.x == self.position.x and \
            position.y == (self.position.y + (self.player.y_direction * 2)) and \
            self.position == self.initial_position and \
            position.piece is None:
            return True
        # attack move into a position occupied by enemy
        elif (position.x == (self.position.x + 1) or position.x == (self.position.x - 1)) and \
            position.y == (self.position.y + self.player.y_direction) and \
            position.piece is not None and \
            position.piece.player != self.player:
            return True
        return False


class Rook(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self.same_position(position):
            return False
        # own piece in the way
        elif self.own_piece_interfering(position):
            return False
        elif self.straight_clear(position):
            return True
        return False


class Bishop(Piece):
    def can_move(self, position: Position) -> bool:
        board = position.board
        # same position
        if self.same_position(position):
            return False
        # own piece in the way
        elif self.own_piece_interfering(position):
            return False
        elif self.diagonal_clear(position):
            return True
        return False


class Knight(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self.same_position(position):
            return False
        # own piece in the way
        elif self.own_piece_interfering(position):
            return False
        elif (abs(position.x - self.position.x) == 1 and abs(position.y - self.position.y) == 2) or (abs(position.x - self.position.x) == 2 and abs(position.y - self.position.y) == 1):
            return True
        return False


class Queen(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self.same_position(position):
            return False
        # own piece in the way
        elif self.own_piece_interfering(position):
            return False
        elif self.straight_clear(position) or self.diagonal_clear(position):
            return True
        return False


class King(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self.same_position(position):
            return False
        # own piece in the way
        # TODO: account for castling
        elif self.own_piece_interfering(position):
            return False
        elif abs(position.x - self.position.x) <= 1 and abs(position.y - self.position.y) <= 1:
            return True
        return False



def get_center(parent_surface: pygame.Surface, child_surface: pygame.Surface):
    return ((parent_surface.get_width() - child_surface.get_width()) / 2,
            (parent_surface.get_height() - child_surface.get_height()) / 2)


class State(IntEnum):
    PIECE_SELECT = 0
    MOVE = 1


class GameSession:
    def __init__(self):
        self.playtime = 0.0
        self.state = State.PIECE_SELECT
        self.selected_piece = None


class Pygame:
    def __init__(self, width: int, height: int, fps: int = 20):
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
        self.game_pieces = pygame.sprite.Group()

        self.players = [Player('White', y_direction=1), Player('Black', y_direction=-1)]
        player_cycle = cycle(self.players)
        self.next_player = lambda: next(player_cycle)
        self.active_player = self.next_player()
        # self.active_player = self.game_session.active_player
        self.state = self.game_session.state
        self.selected_piece = self.game_session.selected_piece

        self.board = Board()
        for position in self.board.positions:
            self.all_sprites.add(position)
        # for x in range(8):
        #     pawn = Pawn('icons/pawn80x80.png', self.board.positions[x][1], 0)
        #     self.game_pieces.add(pawn)
        #     self.all_sprites.add(pawn)
        self.pieces = []
        self._load_pieces()

    def _load_pieces(self):

        layout_filename = 'piece_layout.json'
        icon_filename = 'icons.json'
        # spritesheet_filename = 'icons/chess_pieces.bmp'
        # piece_spritesheet = SpriteSheet(spritesheet_filename)
        # piece_images = piece_spritesheet.load_grid_images(2, 6, x_margin=64, x_padding=72, y_margin=68, y_padding=48)
        piece_types = [King, Queen, Rook, Bishop, Knight, Pawn]
        # piece_number = 0
        with open(layout_filename) as layout_config_file:
            layout_config = json.load(layout_config_file)
        with open(icon_filename) as icon_config_file:
            icon_config = json.load(icon_config_file)
        for player in reversed(self.players):
            for piece_type in piece_types:
                positions = layout_config.get(player.color).get(piece_type.__name__)
                for position in positions:
                    piece = piece_type(player)
                    # piece.set_image(piece_images[piece_number])
                    piece.set_image(icon_config.get(player.color).get(piece_type.__name__))
                    piece.set_position(self.board.positions[position.get('x')][position.get('y')])
                    self.pieces.append(piece)
                    self.game_pieces.add(piece)
                    self.all_sprites.add(piece)
                # piece_number += 1

        # for image in piece_images:
        #     piece = GamePiece()
        #     piece.set_image(image)
        #     self.game_pieces.add(piece)
        #     self.all_sprites.add(piece)
        #     self.pieces.append(piece)

    def run(self):
        """
        Main event loop
        :return:
        """
        running = True
        first_loop = True
        while running:
            milliseconds = self.clock.tick(self.fps)
            self.game_session.playtime += milliseconds / 1000.0

            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key in [K_ESCAPE, K_q]):
                    running = False
                if event.type == MOUSEBUTTONDOWN:
                    self.act(event.pos, event.button)

            if first_loop:
                self.draw()

        pygame.quit()

    def draw(self):
        self.background.fill((255, 255, 255))

        for sprite in self.all_sprites:
            self.screen.blit(sprite.surface, sprite.rect)

        # self.draw_text(
        #     f"Playtime: {self.game_session.playtime:.2f}")

        pygame.display.flip()
        self.screen.blit(self.background, (0, 0))

    def act(self, pos: tuple, button: int):
        if button == 1 and self.board.rect.collidepoint(pos):
            player = self.active_player
            if self.state == State.PIECE_SELECT:
                for piece in player.pieces:
                    if piece.rect.collidepoint(*pos):
                        print(f'Selected {player.color} {piece.name}')
                        self.state = State.MOVE
                        self.selected_piece = piece
            elif self.state == State.MOVE:
                for row in self.board.positions:
                    for position in row:
                        if position.rect.collidepoint(*pos):
                            if self.selected_piece.can_move(position):
                                print(f'Moving {player.color} {self.selected_piece.name} to {position}')
                                if position.piece is not None:
                                    position.piece.player.pieces.remove(position.piece)
                                    position.piece.kill()
                                self.selected_piece.set_position(position)
                                self.selected_piece = None
                                self.draw()
                                self.state = State.PIECE_SELECT
                                self.active_player = self.next_player()
                            else:
                                print(f'Not a legal move')
        elif button == 3 and self.state == State.MOVE:
            self.state = State.PIECE_SELECT
            self.selected_piece = None
            print('Canceled piece selection')

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
