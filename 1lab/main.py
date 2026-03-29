from abc import ABC, abstractmethod


class Piece(ABC):
    def __init__(self, color, row, col):
        self.color = color
        self.row = row
        self.col = col
        self.has_moved = False
        self.symbol = '?'

    @abstractmethod
    def get_possible_moves(self, board):
        pass

    def get_valid_moves(self, board):
        moves = self.get_possible_moves(board)
        valid = []
        for r, c in moves:
            if board.is_safe_move(self.row, self.col, r, c, self.color):
                valid.append((r, c))
        return valid

    def __str__(self):
        return self.symbol


class Move:
    def __init__(self, from_row, from_col, to_row, to_col, piece, captured):
        self.from_row = from_row
        self.from_col = from_col
        self.to_row = to_row
        self.to_col = to_col
        self.piece = piece
        self.captured = captured


class Board:
    def __init__(self, mode='chess'):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.mode = mode
        self._setup()

    def _setup(self):
        if self.mode == 'chess':
            for c in range(8):
                self.grid[1][c] = Pawn('black', 1, c)
                self.grid[6][c] = Pawn('white', 6, c)

            pieces = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
            for c, cls in enumerate(pieces):
                self.grid[0][c] = cls('black', 0, c)
                self.grid[7][c] = cls('white', 7, c)
        else:
            for r in range(3):
                for c in range(8):
                    if (r + c) % 2 == 1:
                        self.grid[r][c] = Checker('black', r, c)
            for r in range(5, 8):
                for c in range(8):
                    if (r + c) % 2 == 1:
                        self.grid[r][c] = Checker('white', r, c)

    def is_in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def is_empty(self, r, c):
        return self.is_in_bounds(r, c) and self.grid[r][c] is None

    def has_own(self, r, c, color):
        return (self.is_in_bounds(r, c) and self.grid[r][c] and
                self.grid[r][c].color == color)

    def has_enemy(self, r, c, color):
        return (self.is_in_bounds(r, c) and self.grid[r][c] and
                self.grid[r][c].color != color)

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and isinstance(p, King) and p.color == color:
                    return (r, c)
        return None

    def is_attacked(self, r, c, color):
        for row in range(8):
            for col in range(8):
                p = self.grid[row][col]
                if p and p.color != color:
                    if isinstance(p, King):
                        moves = p.get_possible_moves(self, check_castle=False)
                    else:
                        moves = p.get_possible_moves(self)
                    if (r, c) in moves:
                        return True
        return False

    def is_threatened(self, r, c, color):
        for row in range(8):
            for col in range(8):
                p = self.grid[row][col]
                if p and p.color != color and isinstance(p, Checker):
                    captures = p.get_captures(self)
                    for (cr, cc, _, _) in captures:
                        if cr == r and cc == c:
                            return True
        return False

    def is_safe_move(self, fr, fc, tr, tc, color):
        piece = self.grid[fr][fc]
        captured = self.grid[tr][tc]

        self.grid[tr][tc] = piece
        self.grid[fr][fc] = None
        if piece:
            piece.row, piece.col = tr, tc

        king = self.find_king(color)
        in_check = self.is_attacked(king[0], king[1], color) if king else False

        self.grid[fr][fc] = piece
        self.grid[tr][tc] = captured
        if piece:
            piece.row, piece.col = fr, fc
        if captured:
            captured.row, captured.col = tr, tc

        return not in_check

    def move(self, fr, fc, tr, tc):
        piece = self.grid[fr][fc]
        if not piece:
            return False, None

        if (tr, tc) not in piece.get_valid_moves(self):
            return False, None

        captured = self.grid[tr][tc]

        if self.mode == 'checkers' and isinstance(piece, Checker):
            dr = tr - fr
            dc = tc - fc
            if abs(dr) == 2 and abs(dc) == 2:
                cr, cc = fr + dr // 2, fc + dc // 2
                if (self.is_in_bounds(cr, cc) and self.grid[cr][cc] and
                        self.grid[cr][cc].color != piece.color):
                    self.grid[cr][cc] = None
            elif abs(dr) > 2 or abs(dc) > 2:
                step_r = 1 if dr > 0 else -1
                step_c = 1 if dc > 0 else -1
                r, c = fr + step_r, fc + step_c
                while r != tr and c != tc:
                    if (self.grid[r][c] and
                            self.grid[r][c].color != piece.color):
                        self.grid[r][c] = None
                    r += step_r
                    c += step_c

        if isinstance(piece, King) and abs(tc - fc) == 2:
            if tc > fc:
                rook = self.grid[piece.row][7]
                self.grid[piece.row][5] = rook
                self.grid[piece.row][7] = None
                rook.row, rook.col = piece.row, 5
                rook.has_moved = True
            else:
                rook = self.grid[piece.row][0]
                self.grid[piece.row][3] = rook
                self.grid[piece.row][0] = None
                rook.row, rook.col = piece.row, 3
                rook.has_moved = True

        self.grid[tr][tc] = piece
        self.grid[fr][fc] = None
        piece.row, piece.col = tr, tc
        piece.has_moved = True

        if self.mode == 'checkers' and isinstance(piece, Checker):
            if not piece.is_king and (
                    (piece.color == 'white' and tr == 0) or
                    (piece.color == 'black' and tr == 7)):
                piece.is_king = True
                piece.symbol = '★' if piece.color == 'white' else '☆'

        return True, captured

    def undo(self, move):
        self.grid[move.from_row][move.from_col] = move.piece
        self.grid[move.to_row][move.to_col] = move.captured
        move.piece.row, move.piece.col = move.from_row, move.from_col
        if move.captured:
            move.captured.row, move.captured.col = move.to_row, move.to_col


class Pawn(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '♟' if color == 'white' else '♙'

    def get_possible_moves(self, board):
        moves = []
        direction = -1 if self.color == 'white' else 1

        if board.is_empty(self.row + direction, self.col):
            moves.append((self.row + direction, self.col))
            if not self.has_moved and board.is_empty(
                    self.row + 2 * direction, self.col):
                moves.append((self.row + 2 * direction, self.col))

        for dc in [-1, 1]:
            if board.has_enemy(
                    self.row + direction, self.col + dc, self.color):
                moves.append((self.row + direction, self.col + dc))

        return moves


class Rook(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '♜' if color == 'white' else '♖'

    def get_possible_moves(self, board):
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            r, c = self.row + dr, self.col + dc
            while board.is_in_bounds(r, c):
                if board.is_empty(r, c):
                    moves.append((r, c))
                elif board.has_enemy(r, c, self.color):
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
        return moves


class Knight(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '♞' if color == 'white' else '♘'

    def get_possible_moves(self, board):
        moves = []
        offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for dr, dc in offsets:
            r, c = self.row + dr, self.col + dc
            if board.is_in_bounds(r, c):
                if not board.has_own(r, c, self.color):
                    moves.append((r, c))
        return moves


class Bishop(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '♝' if color == 'white' else '♗'

    def get_possible_moves(self, board):
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = self.row + dr, self.col + dc
            while board.is_in_bounds(r, c):
                if board.is_empty(r, c):
                    moves.append((r, c))
                elif board.has_enemy(r, c, self.color):
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
        return moves


class Queen(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '♛' if color == 'white' else '♕'

    def get_possible_moves(self, board):
        moves = []
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]
        for dr, dc in directions:
            r, c = self.row + dr, self.col + dc
            while board.is_in_bounds(r, c):
                if board.is_empty(r, c):
                    moves.append((r, c))
                elif board.has_enemy(r, c, self.color):
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
        return moves


class King(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '♚' if color == 'white' else '♔'

    def get_possible_moves(self, board, check_castle=True):
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = self.row + dr, self.col + dc
                if board.is_in_bounds(r, c):
                    if not board.has_own(r, c, self.color):
                        moves.append((r, c))

        if check_castle and not self.has_moved:
            if self.color == 'white' and self.row == 7 and self.col == 4:
                rook = board.grid[7][7]
                if (rook and isinstance(rook, Rook) and not rook.has_moved and
                        board.is_empty(7, 5) and board.is_empty(7, 6)):
                    if (not board.is_attacked(7, 4, self.color) and
                            not board.is_attacked(7, 5, self.color) and
                            not board.is_attacked(7, 6, self.color)):
                        moves.append((7, 6))

                rook = board.grid[7][0]
                if (rook and isinstance(rook, Rook) and not rook.has_moved and
                        board.is_empty(7, 3) and board.is_empty(7, 2) and
                        board.is_empty(7, 1)):
                    if (not board.is_attacked(7, 4, self.color) and
                            not board.is_attacked(7, 3, self.color) and
                            not board.is_attacked(7, 2, self.color)):
                        moves.append((7, 2))

            elif self.color == 'black' and self.row == 0 and self.col == 4:
                rook = board.grid[0][7]
                if (rook and isinstance(rook, Rook) and not rook.has_moved and
                        board.is_empty(0, 5) and board.is_empty(0, 6)):
                    if (not board.is_attacked(0, 4, self.color) and
                            not board.is_attacked(0, 5, self.color) and
                            not board.is_attacked(0, 6, self.color)):
                        moves.append((0, 6))

                rook = board.grid[0][0]
                if (rook and isinstance(rook, Rook) and not rook.has_moved and
                        board.is_empty(0, 3) and board.is_empty(0, 2) and
                        board.is_empty(0, 1)):
                    if (not board.is_attacked(0, 4, self.color) and
                            not board.is_attacked(0, 3, self.color) and
                            not board.is_attacked(0, 2, self.color)):
                        moves.append((0, 2))

        return moves


class Car(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '🚗'

    def get_possible_moves(self, board):
        moves = []
        offsets = [
            (-4, -2), (-4, 2), (4, -2), (4, 2),
            (-2, -4), (-2, 4), (2, -4), (2, 4)
        ]
        for dr, dc in offsets:
            r, c = self.row + dr, self.col + dc
            if board.is_in_bounds(r, c):
                if not board.has_own(r, c, self.color):
                    moves.append((r, c))
        return moves


class Ship(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '⛵'

    def get_possible_moves(self, board):
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            r, c = self.row + dr, self.col + dc
            steps = 0
            while steps < 3 and board.is_in_bounds(r, c):
                if board.is_empty(r, c):
                    moves.append((r, c))
                elif board.has_enemy(r, c, self.color):
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
                steps += 1
        return moves


class Plane(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '✈'

    def get_possible_moves(self, board):
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = self.row + dr, self.col + dc
            steps = 0
            while steps < 4 and board.is_in_bounds(r, c):
                if board.is_empty(r, c):
                    moves.append((r, c))
                elif board.has_enemy(r, c, self.color):
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
                steps += 1
        return moves


class Checker(Piece):
    def __init__(self, color, row, col):
        super().__init__(color, row, col)
        self.symbol = '⬤' if color == 'white' else '○'
        self.is_king = False

    def get_possible_moves(self, board):
        captures = self.get_all_captures(
            board, self.row, self.col, self.color, self.is_king)
        if captures:
            if captures:
                return [(cr, cc) for (cr, cc, _, _) in captures[0]]
            return []

        moves = []
        direction = -1 if self.color == 'white' else 1

        for dc in [-1, 1]:
            r, c = self.row + direction, self.col + dc
            if board.is_in_bounds(r, c) and board.is_empty(r, c):
                moves.append((r, c))

        if self.is_king:
            for dr in [-1, 1]:
                for dc in [-1, 1]:
                    r, c = self.row + dr, self.col + dc
                    while board.is_in_bounds(r, c):
                        if board.is_empty(r, c):
                            moves.append((r, c))
                        else:
                            break
                        r += dr
                        c += dc
        return moves

    def get_all_captures(self, board, row, col, color, is_king, depth=0):
        captures = []
        direction = -1 if color == 'white' else 1

        if not is_king:
            for dc in [-1, 1]:
                r, c = row + direction, col + dc
                if board.is_in_bounds(r, c) and board.has_enemy(r, c, color):
                    cr, cc = r + direction, c + dc
                    if (board.is_in_bounds(cr, cc) and
                            board.is_empty(cr, cc)):
                        enemy = board.grid[r][c]
                        board.grid[r][c] = None
                        next_captures = self.get_all_captures(
                            board, cr, cc, color, is_king, depth + 1)
                        board.grid[r][c] = enemy

                        if next_captures:
                            for nc in next_captures:
                                captures.append([(cr, cc, r, c)] + nc)
                        else:
                            captures.append([(cr, cc, r, c)])

        else:
            for dr in [-1, 1]:
                for dc in [-1, 1]:
                    r, c = row + dr, col + dc
                    while board.is_in_bounds(r, c):
                        if board.has_enemy(r, c, color):
                            cr, cc = r + dr, c + dc
                            if (board.is_in_bounds(cr, cc) and
                                    board.is_empty(cr, cc)):
                                enemy = board.grid[r][c]
                                board.grid[r][c] = None
                                next_captures = self.get_all_captures(
                                    board, cr, cc, color, is_king, depth + 1)
                                board.grid[r][c] = enemy

                                if next_captures:
                                    for nc in next_captures:
                                        captures.append([(cr, cc, r, c)] + nc)
                                else:
                                    captures.append([(cr, cc, r, c)])
                            break
                        if not board.is_empty(r, c):
                            break
                        r += dr
                        c += dc

        return captures

    def get_captures(self, board):
        all_captures = self.get_all_captures(
            board, self.row, self.col, self.color, self.is_king)
        if all_captures:
            return [c[0] for c in all_captures]
        return []


class Game:
    def __init__(self, mode='chess'):
        self.board = Board(mode)
        self.mode = mode
        self.turn = 'белые'
        self.history = []
        self.threatened = []

    def _update_threatened(self):
        self.threatened = []
        current_color = 'white' if self.turn == 'белые' else 'black'

        for r in range(8):
            for c in range(8):
                p = self.board.grid[r][c]
                if p and p.color == current_color:
                    if self.mode == 'checkers' and isinstance(p, Checker):
                        if self.board.is_threatened(r, c, current_color):
                            self.threatened.append((r, c))
                    elif self.board.is_attacked(r, c, current_color):
                        self.threatened.append((r, c))

    def _in_check(self, color):
        king = self.board.find_king(color)
        if king:
            return self.board.is_attacked(king[0], king[1], color)
        return False

    def _has_moves(self, color):
        for r in range(8):
            for c in range(8):
                p = self.board.grid[r][c]
                if p and p.color == color and p.get_valid_moves(self.board):
                    return True
        return False

    def _coord(self, s):
        if len(s) != 2:
            return None
        cols = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        col = cols.get(s[0].lower())
        if col is None:
            return None
        try:
            row = 8 - int(s[1])
        except ValueError:
            return None
        if 0 <= row < 8:
            return (row, col)
        return None

    def _promote(self, r, c):
        p = self.board.grid[r][c]
        if isinstance(p, Pawn):
            if ((p.color == 'white' and r == 0) or
                    (p.color == 'black' and r == 7)):
                print("\nПревращение пешки:")
                print("Q - Ферзь | R - Ладья | B - Слон | K - Конь")
                print("C - Машина | S - Корабль | P - Самолёт")
                ch = input("> ").upper()
                if ch == 'Q':
                    self.board.grid[r][c] = Queen(p.color, r, c)
                elif ch == 'R':
                    self.board.grid[r][c] = Rook(p.color, r, c)
                elif ch == 'B':
                    self.board.grid[r][c] = Bishop(p.color, r, c)
                elif ch == 'K':
                    self.board.grid[r][c] = Knight(p.color, r, c)
                elif ch == 'C':
                    self.board.grid[r][c] = Car(p.color, r, c)
                elif ch == 'S':
                    self.board.grid[r][c] = Ship(p.color, r, c)
                elif ch == 'P':
                    self.board.grid[r][c] = Plane(p.color, r, c)
                else:
                    self.board.grid[r][c] = Queen(p.color, r, c)
                return True
        return False

    def display(self, selected=None, moves=None):
        print("\n   a  b  c  d  e  f  g  h")
        print("  -------------------------")
        for r in range(8):
            print(f"{8 - r}|", end="")
            for c in range(8):
                p = self.board.grid[r][c]
                if selected and (r, c) == selected:
                    print(f"[{p if p else ' '}]", end="")
                elif moves and (r, c) in moves:
                    if p:
                        print(f"*{p}*", end="")
                    else:
                        print(" · ", end="")
                elif (r, c) in self.threatened:
                    print(f"!{p if p else ' '}!", end="")
                else:
                    print(f" {p if p else '.'} ", end="")
            print(f"|{8 - r}")
        print("  -------------------------")
        print("   a  b  c  d  e  f  g  h")
        check_color = 'white' if self.turn == 'белые' else 'black'
        if self.mode == 'chess' and self._in_check(check_color):
            print(f"⚠️  {self.turn.upper()} ПОД ШАХОМ!")
        print(f"Ход: {self.turn}")

    def play(self):
        while True:
            self._update_threatened()
            self.display()

            current_color = 'white' if self.turn == 'белые' else 'black'
            if not self._has_moves(current_color):
                if self.mode == 'chess' and self._in_check(current_color):
                    print(f"Мат! {self.turn} проиграли")
                else:
                    print("Пат!")
                break

            print("\nКоманды: ход (e2 e4), отмена (undo), выход (quit)")
            cmd = input("> ").strip().lower()

            if cmd == 'quit':
                break
            elif cmd == 'undo':
                if self.history:
                    self.board.undo(self.history.pop())
                    self.turn = 'чёрные' if self.turn == 'белые' else 'белые'
                    print("Ход отменён")
                else:
                    print("Нечего отменять")
                continue

            parts = cmd.split()
            if len(parts) != 2:
                print("Формат: e2 e4")
                continue

            fr = self._coord(parts[0])
            to = self._coord(parts[1])
            if not fr or not to:
                print("Неверные координаты")
                continue

            fr_r, fr_c = fr
            to_r, to_c = to
            piece = self.board.grid[fr_r][fr_c]

            if not piece or piece.color != current_color:
                print("Не ваша фигура")
                continue

            moves = piece.get_valid_moves(self.board)
            self.display(selected=(fr_r, fr_c), moves=moves)

            if (to_r, to_c) not in moves:
                print("Неверный ход")
                continue

            captured = self.board.grid[to_r][to_c]
            move = Move(fr_r, fr_c, to_r, to_c, piece, captured)

            ok, _ = self.board.move(fr_r, fr_c, to_r, to_c)
            if ok:
                self.history.append(move)
                if self.mode == 'chess':
                    self._promote(to_r, to_c)
                self.turn = 'чёрные' if self.turn == 'белые' else 'белые'
            else:
                print("Ход невозможен")

    def run(self):
        print("Шахматы" if self.mode == 'chess' else "Шашки")
        self.play()


def main():
    print("1 - Шахматы")
    print("2 - Шашки")
    ch = input("> ")
    game = Game('chess' if ch != '2' else 'checkers')
    game.run()


if __name__ == "__main__":
    main()
