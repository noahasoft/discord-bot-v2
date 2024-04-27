from math import prod
import random
from itertools import cycle
from collections import Counter
from enum import Enum

from dataclasses import dataclass
from typing import Any
import warnings

ROUNDING_PRECISION = 6


class RewardType(Enum):
    MONEY = 0
    SPIN = 1


class Reward:
    """
    A reward can be money or a free spin.
    """

    def __init__(self, reward_type: RewardType, value: float):
        self.reward_type = reward_type
        self.value = value

    def __repr__(self) -> str:
        return f"Reward({self.reward_type}, {self.value})"

    def __str__(self) -> str:
        return f"{self.value} {self.reward_type.name.lower()}"

    # A free game is always better than money
    def __gt__(self, other: "Reward") -> bool:
        if self.reward_type == RewardType.SPIN:
            return True
        if other.reward_type == RewardType.SPIN:
            return False
        return self.value > other.value

    def __eq__(self, other) -> bool:
        if not isinstance(other, Reward):
            return False
        return self.reward_type == other.reward_type and self.value == other.value


@dataclass
class Symbol:
    """
    Base class for a symbol in the slot machine.
    """

    name: str

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"Symbol({self.name})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Symbol):
            return False
        return self.name == other.name


class AnySymbol(Symbol):
    """
    A symbol that can match any other symbol.
    """

    def __init__(self):
        super().__init__("Any")

    def __str__(self) -> str:
        return "*"

    def __repr__(self) -> str:
        return "AnySymbol()"

    def __eq__(self, _: Any) -> bool:
        return True

    def __hash__(self) -> int:
        return hash("Any")

    def __ne__(self, _: Any) -> bool:
        return False


class NotSymbol(Symbol):
    """
    A symbol that is not equal to the given symbol.
    """

    @classmethod
    def from_symbol(cls, symbol: Symbol) -> "NotSymbol":
        return cls(symbol.name)

    def __str__(self) -> str:
        return f"#{self.name}"

    def __repr__(self) -> str:
        return f"NotSymbol({self.name})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Symbol):
            return False
        return self.name != other.name

    def __hash__(self) -> int:
        return hash(f"#{self.name}")

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, Symbol):
            return True
        return self.name == other.name


class ScatterSymbol(Symbol):
    """
    A scatter symbol is a special symbol that can appear anywhere on
    the reels to trigger a win.
    """

    @classmethod
    def from_symbol(cls, symbol: Symbol) -> "ScatterSymbol":
        return cls(symbol.name)

    def __str__(self) -> str:
        return f"{self.name}.s"

    def __repr__(self) -> str:
        return f"ScatterSymbol({self.name})"

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Symbol):
            return False
        return self.name == other.name


class Payline:
    """
    A payline is a sequence of indices that represent a winning combination.
    """

    def __init__(self, indices: list[int]):
        self.indices = indices

    def __getitem__(self, idx: int) -> int:
        return self.indices[idx]

    def __str__(self) -> str:
        return str(self.indices)

    def __repr__(self) -> str:
        return f"Payline({self.indices})"

    def adapt(self, reel: "Reelstrip") -> None:
        """Adapt the payline to the reelstrip by extending the indices"""
        self.indices.append(self.indices[-1])


class Window:
    """
    A window represents the layout of the slot machine reels.
    It is defined by the number of rows per column(wheel).
    A window can be used to create common paylines.
    All paylines are zero-indexed.
    Symbols that appear in a window are called "normal" symbols.
    """

    rows_per_column: list[int]

    def __init__(self, rows_per_column: list[int]):
        self.rows_per_column = rows_per_column

    def __repr__(self) -> str:
        return f"Window(rows_per_column={self.rows_per_column})"

    @property
    def cols(self) -> int:
        return len(self.rows_per_column)

    @property
    def max_rows(self) -> int:
        return max(self.rows_per_column)

    @property
    def min_rows(self) -> int:
        return min(self.rows_per_column)

    def adapt(self, reel: "Reelstrip") -> None:
        """Adapt the window to the reelstrip by padding."""
        if len(self.rows_per_column) < len(reel.symbols):
            for _ in range(len(reel.symbols) - len(self.rows_per_column)):
                self.rows_per_column.append(self.rows_per_column[-1])

    # Convenience methods for creating common paylines
    def centerline(self) -> Payline:
        return Payline([rows // 2 for rows in self.rows_per_column])

    def topline(self) -> Payline:
        return Payline([0] * self.cols)

    def bottomline(self) -> Payline:
        return Payline([rows - 1 for rows in self.rows_per_column])

    def tl_diag(self) -> Payline:
        return Payline(
            [min(i, rows - 1) for i, rows in enumerate(self.rows_per_column)]
        )

    def tr_diag(self) -> Payline:
        return Payline(
            [rows - 1 - min(i, rows - 1) for i, rows in enumerate(self.rows_per_column)]
        )


class Reelstrip:
    """
    A reelstrip is a list of symbols that can appear on a reel.
    Each symbol has a corresponding count, which determines the probability
    of the symbol appearing on the reel.
    """

    def __init__(self, symbols: list[Symbol], counts: list[int], shuffle: bool = True):
        self._base_symbols = symbols
        self.symbols = self._build_wheel(symbols, counts, shuffle)
        self.counts = counts

    def __iter__(self):
        count = {}
        for symbol in sorted(self.symbols, key=lambda x: x.name):
            count[symbol] = count.get(symbol, 0) + 1
            yield str(symbol), count[symbol]

    def _build_wheel(
        self, symbols: list[Symbol], counts: list[int], shuffle: bool = True
    ) -> list[Symbol]:
        """Build the wheel based on the symbols and counts."""
        symbols = sum([[symbol] * count for symbol, count in zip(symbols, counts)], [])
        if shuffle:
            random.shuffle(symbols)
        return symbols

    def spin(self, window: Window) -> list[Symbol]:
        """
        Spin the reelstrip and return a window of symbols.
        """
        result = []
        for rows in window.rows_per_column:
            center = random.randint(0, len(self.symbols) - 1)
            wrapped_symbols = cycle(self.symbols)
            # Advance the iterator to the center position of this column
            for _ in range(center - rows // 2):
                next(wrapped_symbols)
            column_result = [next(wrapped_symbols) for _ in range(rows)]
            result.append(column_result[0])
        return result

    def get_count(self, symbol: Symbol) -> float:
        return Counter(self.symbols)[symbol]

    def __repr__(self) -> str:
        return f"Reelstrip({dict(self)})"

    def __str__(self) -> str:
        return str(dict(self))

    def copy(self) -> "Reelstrip":
        return Reelstrip(self._base_symbols, self.counts)


class PayRule:
    """
    A pay rule defines a winning combination of symbols and the payout.
    Special symbols such as NotSymbol and AnySymbol can be used to define
    more complex pay rules.
    """

    def __init__(self, symbol_pattern: list[Symbol], reward: Reward):
        self.symbol_pattern = symbol_pattern
        self.reward = reward

    def __repr__(self) -> str:
        rule_string = f"[{', '.join(str(symbol) for symbol in self.symbol_pattern)}]"
        return f"PayRule({rule_string}, {self.reward})"

    def __str__(self) -> str:
        return self.__repr__()

    def evaluate(self, symbols: list[Symbol]) -> bool:
        """Check if symbol list contains the winning pattern as a substring."""
        return any(
            self.symbol_pattern == symbols[idx : idx + len(self.symbol_pattern)]
            for idx in range(len(symbols))
        )


class AnyPayRule:
    """
    An 'Any' pay rule defines a special winning combination of symbols
    that can match any other symbol.
    """

    def __init__(self, symbol_pattern: list[Symbol], reward: Reward):
        self.reward = reward
        self._base_symbol_pattern = symbol_pattern
        self._all_symbols = set(symbol_pattern) - {AnySymbol()}
        self.symbol_patterns = self._generate_symbol_patterns(symbol_pattern)

    def _generate_symbol_patterns(self, pattern: list[Symbol], idx: int = 0):
        if idx == len(pattern):
            return [pattern.copy()]  # Return a copy of the current pattern

        current_symbol = pattern[idx]
        if isinstance(current_symbol, AnySymbol):
            combinations = []
            # Iterate through all possible symbols to replace the 'Any' symbol
            for symbol in self._all_symbols:
                pattern[idx] = symbol
                combinations.extend(self._generate_symbol_patterns(pattern, idx + 1))
            pattern[idx] = current_symbol  # Restore original symbol after processing
            return combinations
        else:
            return self._generate_symbol_patterns(pattern, idx + 1)

    def __repr__(self) -> str:
        return f"AnyPayRule({self._base_symbol_pattern}, {self.reward})"


class ScatterPayRule(PayRule):
    def __init__(self, symbol_pattern: list[Symbol], min_count: int, reward: Reward):
        super().__init__(symbol_pattern, reward)
        self.min_count = min_count

    def __repr__(self) -> str:
        symbol_str = (
            "[" + ", ".join(symbol.__repr__() for symbol in self.symbol_pattern) + "]"
        )
        return f"ScatterPayRule({symbol_str}, min_count={self.min_count}, reward={self.reward})"

    def __str__(self) -> str:
        symbol_str = (
            "[" + ", ".join(str(symbol) for symbol in self.symbol_pattern) + "]"
        )
        return f"ScatterPayRule({symbol_str}, min_count={self.min_count}, reward={self.reward})"


class GameBase:
    """
    Define a 'base' game for the slot machine.
    """

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
        is_free_game: bool = False,
    ):
        self.name = name
        self.paylines = paylines
        self.pay_rules = pay_rules
        self.reels = reels
        self.is_free_game = is_free_game

    def __repr__(self) -> str:
        return f"GameBase({self.name})"


class Machine:
    """
    A slot machine that can play multiple games. This is also the
    main class that manages the slot machine, including pulling the lever,
    evaluating the result, and calculating the probability of winning.
    """

    current_game_idx: int
    games: list[GameBase]
    window: Window

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
        if len(game.reels) != window.cols:
            raise ValueError("Invalid number of reels.")
        for payline in game.paylines:
            if any(
                idx >= window.rows_per_column[wheel]
                for wheel, idx in enumerate(payline.indices)
            ):
                raise ValueError("Invalid payline index.")

    @property
    def current_game(self) -> GameBase:
        return self.games[self.current_game_idx]

    def pull_lever(self) -> list[list[Symbol]]:
        return [reel.spin(self.window) for reel in self.current_game.reels]

    def evaluate(self, result: list[list[Symbol]]) -> Reward:
        payline_winnings = self.evaluate_payline_winnings(result)
        scatter_winnings = self.evaluate_scatter_winnings(result)
        return max(payline_winnings, scatter_winnings)

    def evaluate_payline_winnings(self, result: list[list[Symbol]]) -> Reward:
        best_payout = Reward(RewardType.MONEY, 0.0)
        for payline in self.current_game.paylines:
            symbols = [result[wheel][idx] for wheel, idx in enumerate(payline.indices)]
            for rule in self.current_game.pay_rules:
                if not isinstance(rule, ScatterPayRule) and rule.evaluate(symbols):
                    best_payout = max(best_payout, rule.reward)
        return best_payout

    def evaluate_scatter_winnings(self, result: list[list[Symbol]]) -> Reward:
        scatter_counts: dict[Symbol, int] = {}
        for reel in result:
            seen_scatters = set()
            for symbol in reel:
                if symbol not in seen_scatters:
                    scatter_counts[symbol] = scatter_counts.get(symbol, 0) + 1
                    seen_scatters.add(symbol)

        best_scatter_payout = Reward(RewardType.MONEY, 0.0)
        for rule in self.current_game.pay_rules:
            if isinstance(rule, ScatterPayRule):
                count = scatter_counts.get(rule.symbol_pattern[0], 0)
                if count >= rule.min_count:
                    best_scatter_payout = max(best_scatter_payout, rule.reward)
        return best_scatter_payout

    @property
    def num_wheels(self) -> int:
        return len(self.current_game.reels)

    def is_on_scoreline(self, wheel_idx: int, row: int) -> bool:
        return any(
            row == payline.indices[wheel_idx] for payline in self.current_game.paylines
        )

    def prob_winning(self, pay_rule: PayRule) -> float:
        """Calculate the probability of winning [0., 1.]"""
        rv = round(
            prod(
                [
                    (
                        reel.get_count(pay_rule.symbol_pattern[idx]) / sum(reel.counts)
                        if pay_rule.symbol_pattern[idx] is not None
                        else sum(reel.counts) / len(reel.symbols)
                    )
                    for game in self.games
                    for idx, reel in enumerate(game.reels)
                ]
            ),
            ROUNDING_PRECISION,
        )
        if rv == 0:
            warnings.warn("The probability of winning is zero. Check the pay rules.")
        return rv

    def hit_rate(self, pay_rule: PayRule) -> float:
        """Calculate the hit rate of the slot machine. [0., inf]"""
        if self.prob_winning == 0:
            return float("inf")
        return round(1 / self.prob_winning(pay_rule), ROUNDING_PRECISION)

    def hit_frequency(self, pay_rule) -> float:
        """Calculate the hit frequency of the slot machine. [0., 1.]"""
        hit_rate = self.hit_rate(pay_rule)
        return round(1 / hit_rate, ROUNDING_PRECISION) if hit_rate != 0 else 1.0

    @property
    def total_prob_winning(self) -> float:
        """Calculate the total probability of winning [0., 1.]"""
        return sum(
            self.prob_winning(rule) for game in self.games for rule in game.pay_rules
        )

    def rtp(self, avg_bet: float) -> float:
        if avg_bet == 0:
            return 1.0
        total_payout = sum(
            rule.reward.value for game in self.games for rule in game.pay_rules
        )
        return round(
            self.total_prob_winning * total_payout / avg_bet, ROUNDING_PRECISION
        )

    @property
    def volatility(self) -> float:
        """Calculate the volatility of the slot machine. [0., inf]"""
        return (
            round(1 / self.rtp(1.0), ROUNDING_PRECISION)
            if self.rtp(1.0) != 0
            else float("inf")
        )

    def add_reel(self, reel: Reelstrip):
        """Add a new reel to the slot machine."""
        self.current_game.reels.append(reel)
        if len(self.current_game.reels) > self.window.cols:
            self.window.rows_per_column.append(self.window.rows_per_column[-1])
        for payline in self.current_game.paylines:
            payline.adapt(reel)

    def expand_window(self, new: Window):
        """Expand the window to accommodate more rows per column."""
        self.window = new
