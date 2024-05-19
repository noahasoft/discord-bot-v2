import random
from enum import Enum
from dataclasses import dataclass
from typing import Any


class BetType(Enum):
    NUMBER = 0
    COLOR = 1
    ODD_EVEN = 2


class Color(Enum):
    RED = "Red"
    BLACK = "Black"
    GREEN = "Green"


EMOJI_COLORS = {Color.RED: "🟥", Color.BLACK: "⬛", Color.GREEN: "🟩"}


@dataclass
class Bet:
    bet_type: BetType
    value: Any
    amount: float

    def __hash__(self) -> int:
        return hash((self.bet_type, self.value, self.amount))


@dataclass
class SpinResult:
    number: int
    color: Color


class RouletteWheel:
    def __init__(self):
        self.numbers = list(range(37))  # 0 to 36
        self.colors = self._build_colors()

    def _build_colors(self):
        colors = {}
        for number in self.numbers:
            if number == 0:
                colors[number] = Color.GREEN
            elif number % 2 == 0:
                colors[number] = Color.RED
            else:
                colors[number] = Color.BLACK
        return colors

    def spin(self) -> SpinResult:
        number = random.choice(self.numbers)
        color = self.colors[number]
        return SpinResult(number, color)


class RouletteGame:
    def __init__(self, seed=None):
        self.wheel = RouletteWheel()
        self.bets = []
        random.seed(seed or None)

    def place_bet(self, bet: Bet):
        self.bets.append(bet)

    def spin_wheel(self) -> SpinResult:
        return self.wheel.spin()

    def evaluate_bets(self, result: SpinResult) -> dict[Bet, float]:
        payouts = {}
        for bet in self.bets:
            if bet.bet_type == BetType.NUMBER:
                if bet.value == result.number:
                    payouts[bet] = bet.amount * 35
                else:
                    payouts[bet] = -bet.amount
            elif bet.bet_type == BetType.COLOR:
                if bet.value == result.color:
                    payouts[bet] = bet.amount * 2
                else:
                    payouts[bet] = -bet.amount
            elif bet.bet_type == BetType.ODD_EVEN:
                if (
                    result.number != 0
                    and (bet.value.lower() == "odd" and result.number % 2 != 0)
                    or (bet.value.lower() == "even" and result.number % 2 == 0)
                ):
                    payouts[bet] = bet.amount * 2
                else:
                    payouts[bet] = 0
            else:
                payouts[bet] = 0
        return payouts

    def clear_bets(self):
        self.bets = []
