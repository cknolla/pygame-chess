#!/usr/bin/env python3
"""
fully-functional 2 player chess
"""
import pickle
import json
import typing
from enum import IntEnum

import pygame

from pygame.locals import (
    K_q,
    K_r,
    K_1,
    K_2,
    K_3,
    K_4,
    K_ESCAPE,
    KEYDOWN,
    MOUSEBUTTONDOWN,
    QUIT,
)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FONT_SIZE = 20


class Player:
    def __init__(self, color: str, y_direction: int):
        self.color = color
        self.y_direction = y_direction
        self.pieces: typing.List[Piece] = []


class Board:
    def __init__(self, width: int, height: int):
        with open('board.json') as board_config_file:
            self.config = json.load(board_config_file)
        self.position_size = self.config.get('Size')
        self.rect = pygame.Rect(0, 0, self.position_size * 8, self.position_size * 8)
        self.rect.left = (width - self.rect.width) / 2
        self.rect.top = (height - self.rect.height) / 2
        self.max_rows = 8
        self.max_cols = 8
        self.positions = [
            [Position(x, y, self) for y in range(self.max_rows)] for x in range(self.max_cols)
        ]


class Position(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, board: Board):
        super().__init__()
        self.x = x
        self.y = y
        self.board: Board = board
        self.piece: Piece = None
        self.previous_piece: Piece = None
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
        return f'{chr(self.x + 97)}{self.y + 1}'

    def update(self):
        """
        Sprite builtin update method
        :return:
        """

    def clear_piece(self):
        self.piece = None


class Piece(pygame.sprite.Sprite):
    def __init__(self, player: Player, icon_config):
        super().__init__()
        self.name = self.__class__.__name__
        self.surface: pygame.Surface = None
        self.image: pygame.image = None
        self.rect: pygame.Rect = None
        self.position: Position = None
        self.previous_position: Position = None
        self.initial_position: Position = None
        self.dirty = False  # has moved
        self.player: Player = player
        player.pieces.append(self)
        self.set_image(icon_config.get(self.player.color).get(self.name))

    def __repr__(self):
        return f'<{self.__class__.__name__} @ {self.position.__repr__()}>'

    def __str__(self):
        return f'{self.__class__.__name__} @ {self.position}'

    def set_image(self, filename: str):
        self.image = pygame.image.load(filename).convert_alpha()
        self.surface = self.image
        self.rect = self.image.get_rect()

    def set_position(self, position: Position):
        self.previous_position = self.position
        if self.position is None:
            self.initial_position = position
        else:
            # unset old position's piece
            self.position.piece = None
        self.position = position
        # reset position's piece to self
        position.previous_piece = position.piece
        position.piece = self
        if position.previous_piece is not None:
            position.previous_piece.player.pieces.remove(position.previous_piece)
        self.rect.left = position.rect.left
        self.rect.top = position.rect.top

    def restore_position(self):
        self.position.piece = self.position.previous_piece
        if self.position.previous_piece is not None:
            self.position.piece.player.pieces.append(self.position.piece)
        self.position = self.previous_position
        self.previous_position.piece = self
        self.rect.left = self.position.rect.left
        self.rect.top = self.position.rect.top

    def can_move(self, position: Position) -> bool:
        raise NotImplementedError('Child class must define a movement')

    def _same_position(self, position: Position) -> bool:
        if position == self.position:
            print('Can\'t move to same position')
            return True
        return False

    def _own_piece_interfering(self, position: Position) -> bool:
        if position.piece is not None and position.piece.player == self.player:
            print(f'Own {position.piece.name} in the way at destination')
            return True
        return False

    def _straight_clear(self, position: Position) -> bool:
        board = position.board
        if position.x == self.position.x and position.y != self.position.y:
            for y in range(min(position.y, self.position.y), max(position.y, self.position.y), 1):
                if y == self.position.y or y == position.y:
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

    def _diagonal_clear(self, position: Position) -> bool:
        board = position.board
        # print(f'start position: {self.position.x},{self.position.y}, end position: {position.x},{position.y}')
        x_dif = position.x - self.position.x
        y_dif = position.y - self.position.y
        if abs(x_dif) == abs(y_dif):
            for dif in range(1, abs(x_dif), 1):
                x = self.position.x + (dif % x_dif) if x_dif > 0 else self.position.x - (dif % abs(x_dif))
                y = self.position.y + (dif % y_dif) if y_dif > 0 else self.position.y - (dif % abs(y_dif))
                if board.positions[x][y].piece is not None:
                    print(
                        f'{board.positions[x][y]} has piece {board.positions[x][y].piece.name}')
                    return False
            return True


class Pawn(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self._same_position(position):
            return False
        # own piece in the way
        elif self._own_piece_interfering(position):
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

    def promotion_check(self) -> bool:
        if (self.player.y_direction < 0 and self.position.y == 0) or (self.player.y_direction > 0 and self.position.y == (self.position.board.max_rows - 1)):
            return True
        return False


class Rook(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self._same_position(position):
            return False
        # own piece in the way
        elif self._own_piece_interfering(position):
            return False
        elif self._straight_clear(position):
            return True
        return False


class Bishop(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self._same_position(position):
            return False
        # own piece in the way
        elif self._own_piece_interfering(position):
            return False
        elif self._diagonal_clear(position):
            return True
        return False


class Knight(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self._same_position(position):
            return False
        # own piece in the way
        elif self._own_piece_interfering(position):
            return False
        elif (abs(position.x - self.position.x) == 1 and abs(position.y - self.position.y) == 2) or (
            abs(position.x - self.position.x) == 2 and abs(position.y - self.position.y) == 1):
            return True
        return False


class Queen(Piece):
    def can_move(self, position: Position) -> bool:
        # same position
        if self._same_position(position):
            return False
        # own piece in the way
        elif self._own_piece_interfering(position):
            return False
        elif self._straight_clear(position) or self._diagonal_clear(position):
            return True
        return False


class King(Piece):
    def can_move(self, position: Position) -> bool:
        board = position.board
        # same position
        if self._same_position(position):
            return False
        # own piece in the way
        elif self._own_piece_interfering(position):
            return False
        elif abs(position.x - self.position.x) <= 1 and abs(position.y - self.position.y) <= 1:
            self.set_position(position)
            if not self.check_check():
                self.restore_position()
                return True
            self.restore_position()
        elif not self.dirty and position.y == self.position.y and abs(position.x - self.position.x) == 2:
            if self.check_check():
                print('Can\'t castle out of check')
                return False
            y = self.position.y
            # determine if legal castle
            if position.x > self.position.x:
                # king-side castle
                rook_position = board.positions[7][y]
                if rook_position.piece is not None and rook_position.piece.name == 'Rook' and rook_position.piece.player == self.player and not rook_position.piece.dirty:
                    rook = rook_position.piece
                    if board.positions[self.position.x + 1][y].piece is None:
                        self.set_position(board.positions[self.position.x + 1][y])
                        if self.check_check():
                            print(f'King would be in check passing through {self.position}')
                            self.restore_position()
                            return False
                        self.restore_position()
                        self.set_position(position)
                        if self.check_check():
                            print(f'King would be in check at {self.position}')
                            self.restore_position()
                            return False
                        rook.dirty = True
                        rook.set_position(board.positions[self.position.x - 1][y])
                        # reset king to original position so standard movement can occur
                        self.restore_position()
                        return True
            else:
                # queen-side castle
                rook_position = board.positions[0][y]
                if rook_position.piece is not None and rook_position.piece.name == 'Rook' and rook_position.piece.player == self.player and not rook_position.piece.dirty:
                    rook = rook_position.piece
                    if board.positions[self.position.x - 1][y].piece is None and board.positions[self.position.x - 2][
                        y].piece is None and board.positions[self.position.x - 3][y].piece is None:
                        self.set_position(board.positions[self.position.x - 1][y])
                        if self.check_check():
                            print(f'King would be in check passing through {self.position}')
                            self.restore_position()
                            return False
                        self.restore_position()
                        self.set_position(position)
                        if self.check_check():
                            print(f'King would be in check at {self.position}')
                            self.restore_position()
                            return False
                        rook.dirty = True
                        rook.set_position(board.positions[self.position.x + 1][y])
                        self.restore_position()
                        return True
        return False

    def check_check(self):
        other_player = game.inactive_player
        for piece in other_player.pieces:
            if piece.can_move(self.position):
                print(f'{other_player.color} {piece.name} at {piece.position} has {self.player.color} King in check')
                return True
        return False

    def checkmate_check(self):
        board = self.position.board
        print('Checkmate checking')
        for piece in self.player.pieces:
            for col in board.positions:
                for position in col:
                    if piece.can_move(position):
                        piece.set_position(position)
                        if not self.check_check():
                            print(f'{piece} can break check')
                            piece.restore_position()
                            return False
                        piece.restore_position()
        return True


# def get_center(parent_surface: pygame.Surface, child_surface: pygame.Surface):
#     return ((parent_surface.get_width() - child_surface.get_width()) / 2,
#             (parent_surface.get_height() - child_surface.get_height()) / 2)


class State(IntEnum):
    PIECE_SELECT = 0
    MOVE = 1
    PAWN_PROMOTION = 2


class GameSession:
    def __init__(self):
        self.playtime = 0.0
        self.state = State.PIECE_SELECT
        self.selected_piece = None


class Game:
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
        self.background.fill((255, 255, 255))
        self.screen.blit(self.background, (0, 0))
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.font = pygame.font.SysFont('mono', FONT_SIZE, bold=True)
        self.check_text = ''
        self.all_sprites = pygame.sprite.Group()
        self.game_pieces = pygame.sprite.Group()
        self.players = [Player('White', y_direction=1), Player('Black', y_direction=-1)]
        self.board = Board(width, height)
        for position in self.board.positions:
            self.all_sprites.add(position)
        self.game_session = None
        self.active_player = None
        self.inactive_player = None
        self.state = None
        self.selected_piece = None
        self.icon_config = self._load_icons()
        self.layout_config = self._load_layout()
        self.pieces = []
        self._reset()

    def _reset(self):
        self.game_session: GameSession = GameSession()
        self.active_player = self.players[0]
        self.inactive_player = self.players[1]
        self.state = self.game_session.state
        self.selected_piece = self.game_session.selected_piece
        self._remove_pieces()
        self._load_pieces()
        self._draw()

    def _next_player(self):
        old_active = self.active_player
        self.active_player = self.inactive_player
        self.inactive_player = old_active

    @staticmethod
    def _load_icons():
        icon_filename = 'icons.json'
        with open(icon_filename) as icon_config_file:
            icon_config = json.load(icon_config_file)
        return icon_config

    @staticmethod
    def _load_layout():
        layout_filename = 'piece_layout.json'
        with open(layout_filename) as layout_config_file:
            layout_config = json.load(layout_config_file)
        return layout_config

    def _load_piece(self, piece_class, player: Player, position: Position):
        piece = piece_class(player, self.icon_config)
        piece.set_position(position)
        self.pieces.append(piece)
        self.game_pieces.add(piece)
        self.all_sprites.add(piece)

    def _load_pieces(self):
        piece_types = [King, Queen, Rook, Bishop, Knight, Pawn]
        for player in reversed(self.players):
            for piece_type in piece_types:
                positions = self.layout_config.get(player.color).get(piece_type.__name__)
                for position in positions:
                    self._load_piece(piece_type, player, self.board.positions[position.get('x')][position.get('y')])

    def _remove_piece(self, piece: Piece):
        piece.player.pieces.remove(piece)
        self.pieces.remove(piece)
        position = piece.position
        position.piece = None
        piece.kill()
        piece.position = None
        # self.game_pieces.remove(piece)
        # self.all_sprites.remove(piece)

    def _remove_pieces(self):
        pieces = self.pieces.copy() # create a temp copy of self.pieces to avoid removing from list while iterating over it
        for piece in pieces:
            self._remove_piece(piece)

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
                elif event.type == MOUSEBUTTONDOWN:
                    self._act(event.pos, event.button)
                elif event.type == KEYDOWN and event.key == K_r:
                    self._reset()
                elif self.state == State.PAWN_PROMOTION and event.type == KEYDOWN and event.key in (K_1, K_2, K_3, K_4):
                    self._pawn_promote(event.key)

        pygame.quit()

    def _act(self, pos: tuple, button: int):
        if button == 1 and self.board.rect.collidepoint(*pos):
            player = self.active_player
            if self.state == State.PIECE_SELECT:
                for piece in player.pieces:
                    if piece.rect.collidepoint(*pos):
                        print(f'Selected {player.color} {piece}')
                        self.state = State.MOVE
                        self.selected_piece = piece
                        self._draw()
            elif self.state == State.MOVE:
                for row in self.board.positions:
                    for position in row:
                        if position.rect.collidepoint(*pos):
                            if self.selected_piece.can_move(position):
                                self.selected_piece.set_position(position)
                                for piece in self.active_player.pieces:
                                    if piece.name == 'King':
                                        # print('Check checking')
                                        if piece.check_check():
                                            print('Move not allowed because player would be in check')
                                            self.selected_piece.restore_position()
                                            return
                                self.selected_piece.restore_position()
                                print(f'Moving {player.color} {self.selected_piece.name} to {position}')
                                if position.piece is not None:
                                    print(f'Defeated {position.piece.player.color} {position.piece}')
                                    # position.piece.player.pieces.remove(position.piece)
                                    # position.piece.kill()
                                    self._remove_piece(position.piece)
                                self.selected_piece.set_position(position)
                                self.selected_piece.dirty = True
                                if self.selected_piece.name == 'Pawn' and self.selected_piece.promotion_check():
                                    self.state = State.PAWN_PROMOTION
                                    self._draw_text(f'Pawn promotion: 1. Queen, 2. Knight, 3. Rook, 4. Bishop', (0, SCREEN_HEIGHT - FONT_SIZE), (0, 0, 0))
                                else:
                                    self._end_turn()
                                self._draw()
                            else:
                                print(f'Movement to {position} not legal')
        elif button == 3 and self.state == State.MOVE:
            self.state = State.PIECE_SELECT
            self.selected_piece = None
            print('Canceled piece selection')
            self._draw()

    def _end_turn(self):
        self.selected_piece = None
        self._next_player()
        for piece in self.active_player.pieces:
            if piece.name == 'King':
                # print('Check checking')
                in_check = piece.check_check()
                if in_check:
                    self.check_text = f'{self.active_player.color} in check!'
                    in_checkmate = piece.checkmate_check()
                    if in_checkmate:
                        self.check_text = f'{self.active_player.color} CHECKMATE. Press R to reset'
                else:
                    self.check_text = ''
        self.state = State.PIECE_SELECT

    def _pawn_promote(self, key):
        position = self.selected_piece.position
        self._remove_piece(self.selected_piece)
        # generate new piece
        if key == K_1:
            piece_type = Queen
        elif key == K_2:
            piece_type = Knight
        elif key == K_3:
            piece_type = Rook
        else:
            piece_type = Bishop
        self._load_piece(piece_type, self.active_player, position)
        self._end_turn()
        self._draw()

    def _draw(self):
        for sprite in self.all_sprites:
            self.screen.blit(sprite.surface, sprite.rect)

        width, height = self._draw_text(f'Player turn: {self.active_player.color}', (0, 0), (0, 0, 0))
        self._draw_text(f'Piece selected: {self.selected_piece.name if self.selected_piece else "None"}', (0, height),
                        (0, 0, 0))
        self._draw_text(self.check_text, (0, height * 2), (200, 0, 0))

        pygame.display.flip()
        self.screen.blit(self.background, (0, 0))

    def _draw_text(self, text: str, position: tuple, color: tuple):
        """
        Draw text in window
        :param text:
        :return:
        """
        font_width, font_height = self.font.size(text)
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, position)
        return font_width, font_height

    def _load(self) -> GameSession:
        try:
            with open('data.dat', 'rb') as file:
                return pickle.load(file)
        except FileNotFoundError:
            return GameSession()

    def _save(self):
        with open('data.dat', 'wb') as file:
            pickle.dump(self.game_session, file)


if __name__ == '__main__':
    game = Game(SCREEN_WIDTH, SCREEN_HEIGHT)
    game.run()
