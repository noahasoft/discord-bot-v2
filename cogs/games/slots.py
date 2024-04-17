import random
from itertools import cycle

from dataclasses import dataclass
from typing import Optional


@dataclass
class SlotSymbol:
    name: str

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)


class SlotPayline:
    def __init__(self, indices: list[int]):
        self.indices = indices

    def __getitem__(self, idx: int) -> int:
        return self.indices[idx]


class SlotWindow:
    def __init__(self, rows: int, cols: int) -> None:
        self.rows, self.cols = rows, cols


class SlotWheel:
    def __init__(self, symbols: list[SlotSymbol], counts: list[float]):
        self.symbols = self.build_wheel(symbols, counts)
        self.counts = counts

    def build_wheel(
        self, symbols: list[SlotSymbol], counts: list[float]
    ) -> list[SlotSymbol]:
        return sum(
            [[symbol] * int(count) for symbol, count in zip(symbols, counts)], []
        )

    def spin(self, window: SlotWindow) -> list[SlotSymbol]:
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

    def get_count(self, symbol: SlotSymbol) -> float:
        return self.counts[self.symbols.index(symbol)]


class PayRule:
    def __init__(
        self, num_symbols: int, payout: float, symbol: Optional[SlotSymbol] = None
    ):
        self.num_symbols = num_symbols
        self.payout = payout
        self.symbol = symbol


@dataclass
class SlotGameBase:
    """Define a 'base' game for the slot machine."""

    name: str
    paylines: list[SlotPayline]
    pay_rules: list[PayRule]
    reels: list[SlotWheel]


class SlotMachine:
    current_game_idx: int

    def __init__(self, games: list[SlotGameBase], window: SlotWindow):
        if len(games) < 1:
            raise ValueError("At least one game must be provided.")
        for game in games:
            if len(game.reels) != window.cols:
                raise ValueError(
                    f"Invalid number of reels: {len(game.reels)}. Must be equal to the number of columns in the window ({window.cols})."
                )
            for payline in game.paylines:
                for idx in payline.indices:
                    if idx >= window.rows:
                        raise ValueError(
                            f"Invalid payline index: {idx}. Must be less than the number of rows in the window ({window.rows})."
                        )
        self.games = games
        self.window = window
        self.current_game_idx = 0

    @classmethod
    def default(cls) -> "SlotMachine":
        return cls(
            [
                SlotGameBase(
                    "g01",
                    [SlotPayline([1, 1, 1])],
                    [PayRule(3, 2.0, SlotSymbol("A"))],
                    [
                        SlotWheel(
                            [
                                SlotSymbol("A"),
                                SlotSymbol("X"),
                            ],
                            [1, 9],
                        )
                        for _ in range(3)
                    ],
                )
            ],
            SlotWindow(3, 3),
        )

    def pull_lever(self) -> list[list[SlotSymbol]]:
        return [
            wheel.spin(self.window) for wheel in self.games[self.current_game_idx].reels
        ]

    def evaluate(self, result: list[list[SlotSymbol]]) -> int:
        """Evaluate the result and return the winnings."""
        for payline in self.games[self.current_game_idx].paylines:
            symbols = []
            for wheel, idx in enumerate(payline.indices):
                symbols.append(result[wheel][idx])
            if len(set(symbols)) == 1:
                for pay_rule in self.games[self.current_game_idx].pay_rules:
                    if pay_rule.num_symbols == len(symbols) and (
                        pay_rule.symbol is None or pay_rule.symbol in symbols
                    ):
                        return pay_rule.payout
        return 0

    @property
    def num_wheels(self) -> int:
        return len(self.games[self.current_game_idx].reels)

    def is_on_scoreline(self, row: int, wheel_idx: int) -> bool:
        for payline in self.games[self.current_game_idx].paylines:
            if row == payline.indices[wheel_idx]:
                return True
        return False


if __name__ == "__main__":
    slot_machine = SlotMachine.default()
    print(slot_machine.pull_lever())
    print(slot_machine.evaluate(slot_machine.pull_lever()))
