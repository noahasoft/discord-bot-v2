from math import prod
import random
from itertools import cycle

from dataclasses import dataclass
from typing import Optional
import warnings

ROUNDING_PRECISION = 6


@dataclass
class Symbol:
    name: str

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)


class Payline:
    def __init__(self, indices: list[int]):
        self.indices = indices

    def __getitem__(self, idx: int) -> int:
        return self.indices[idx]


class Window:
    def __init__(self, rows: int, cols: int) -> None:
        self.rows, self.cols = rows, cols


class Reelstrip:
    def __init__(self, symbols: list[Symbol], counts: list[float]):
        self.symbols = self.build_wheel(symbols, counts)
        self.counts = counts

    def build_wheel(self, symbols: list[Symbol], counts: list[float]) -> list[Symbol]:
        return sum(
            [[symbol] * int(count) for symbol, count in zip(symbols, counts)], []
        )

    def spin(self, window: Window) -> list[Symbol]:
        """Spin the wheel and return the result."""
        num_symbols_to_return = window.rows
        # return a window of symbols, keeping adjacent symbols in the same row
        center = random.randint(0, len(self.symbols) - 1)
        wrapped_symbols = cycle(self.symbols)
        result = []
        for _ in range(center - window.cols // 2):
            next(wrapped_symbols)
        for _ in range(num_symbols_to_return):
            result.append(next(wrapped_symbols))
        return result

    def get_count(self, symbol: Symbol) -> float:
        return self.counts[self.symbols.index(symbol)]


class PayRule:
    def __init__(
        self, num_symbols: int, payout: float, symbol: Optional[Symbol] = None
    ):
        self.num_symbols = num_symbols
        self.payout = payout
        self.symbol = symbol


class GameBase:
    """Define a 'base' game for the slot machine."""

    name: str
    paylines: list[Payline]
    pay_rules: list[PayRule]
    reels: list[Reelstrip]

    def __init__(
        self,
        name: str,
        paylines: list[Payline],
        pay_rules: list[PayRule],
        reels: list[Reelstrip],
    ):
        self.name = name
        self.paylines = paylines
        self.pay_rules = pay_rules
        self.reels = reels


class Machine:
    current_game_idx: int

    def __init__(self, games: list[GameBase], window: Window):
        if not games:
            raise ValueError("At least one game must be provided.")
        for game in games:
            self.validate_game_window(window, game)
        self.games = games
        self.window = window
        self.current_game_idx = 0

    @staticmethod
    def validate_game_window(window: Window, game: GameBase) -> None:
        """Ensure the game and window are compatible."""
        if len(game.reels) != window.cols:
            raise ValueError(
                f"Invalid number of reels: {len(game.reels)}."
                " Must be equal to the number of columns in the window ({window.cols})."
            )
        for payline in game.paylines:
            for idx in payline.indices:
                if idx >= window.rows:
                    raise ValueError(
                        f"Invalid payline index: {idx}. Must be less than the number of rows in"
                        " the window ({window.rows})."
                    )

    @classmethod
    def default(cls) -> "Machine":
        symbol_a = Symbol("A")
        symbol_x = Symbol("X")
        paylines = [Payline([1, 1, 1])]
        pay_rules = [PayRule(3, 1000, symbol_a)]
        reels = [Reelstrip([symbol_a, symbol_x], [1, 9]) for _ in range(3)]
        return cls([GameBase("g01", paylines, pay_rules, reels)], Window(3, 3))

    @property
    def current_game(self):
        return self.games[self.current_game_idx]

    def pull_lever(self) -> list[list[Symbol]]:
        return [reel.spin(self.window) for reel in self.current_game.reels]

    def evaluate(self, result: list[list[Symbol]]) -> int:
        """Evaluate the result and return the winnings."""
        best_payrule: Optional[PayRule] = None
        for payline in self.current_game.paylines:
            symbols = [result[wheel][idx] for wheel, idx in enumerate(payline.indices)]
            for pay_rule in self.current_game.pay_rules:
                if symbols.count(pay_rule.symbol) == pay_rule.num_symbols:
                    if best_payrule is None or pay_rule.payout > best_payrule.payout:
                        best_payrule = pay_rule
        return best_payrule.payout if best_payrule is not None else 0

    @property
    def num_wheels(self) -> int:
        return len(self.current_game.reels)

    def is_on_scoreline(self, row: int, wheel_idx: int) -> bool:
        for payline in self.current_game.paylines:
            if row == payline.indices[wheel_idx]:
                return True
        return False

    @property
    def prob_winning(self) -> float:
        """Calculate the probability of winning [0., 1.]"""
        rv = prod(
            [
                (
                    reel.get_count(pay_rule.symbol) / sum(reel.counts)
                    if pay_rule.symbol is not None
                    else sum(reel.counts) / len(reel.symbols)
                )
                for reel in self.current_game.reels
                for pay_rule in self.current_game.pay_rules
            ]
        )
        if rv == 0:
            warnings.warn("The probability of winning is zero. Check the pay rules.")
        return round(rv, ROUNDING_PRECISION)

    @property
    def hit_rate(self) -> float:
        """Calculate the hit rate of the slot machine. [0., inf]"""
        if self.prob_winning == 0:
            return float("inf")
        return round(1 / self.prob_winning, ROUNDING_PRECISION)

    @property
    def hit_frequency(self) -> float:
        """Calculate the hit frequency of the slot machine. [0., 1.]"""
        return (
            round(1 / self.hit_rate, ROUNDING_PRECISION) if self.hit_rate != 0 else 1.0
        )

    def rtp(self, avg_bet: float) -> float:
        if avg_bet == 0:
            return 1.0
        total_payout = sum(rule.payout for rule in self.current_game.pay_rules)
        return round(self.prob_winning * total_payout / avg_bet, ROUNDING_PRECISION)

    @property
    def volatility(self) -> float:
        """Calculate the volatility of the slot machine. [0., inf]"""
        return (
            round(1 / self.rtp(1.0), ROUNDING_PRECISION)
            if self.rtp(1.0) != 0
            else float("inf")
        )


if __name__ == "__main__":
    slot_machine = Machine.default()
    print(slot_machine.pull_lever())
    print(slot_machine.evaluate(slot_machine.pull_lever()))
    print("prob winning:", slot_machine.prob_winning)
    print("hit rate:", slot_machine.hit_rate)
    print("hit freq:", slot_machine.hit_frequency)
    print("rtp(1):", slot_machine.rtp(1.0))
    print("volatility:", slot_machine.volatility)
