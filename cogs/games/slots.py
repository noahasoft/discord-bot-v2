import random

from dataclasses import dataclass


@dataclass
class SlotSymbol:
    name: str
    value: int

    def __str__(self) -> str:
        return self.name


class SlotWheel:
    def __init__(self, symbols: list[SlotSymbol], probabilities: list[float]):
        self.symbols = symbols
        self.probabilities = probabilities

    def spin(self) -> SlotSymbol:
        return random.choices(self.symbols, self.probabilities, k=1)[0]

    def get_probability(self, symbol: SlotSymbol) -> float:
        return self.probabilities[self.symbols.index(symbol)]


class SlotMachine:
    def __init__(self, wheels: list[SlotWheel]):
        self.wheels = wheels

    @classmethod
    def default(cls) -> "SlotMachine":
        return cls(
            [
                SlotWheel(
                    [
                        SlotSymbol(":cherries:", 2),
                        SlotSymbol(":lemon:", 3),
                        SlotSymbol(":apple:", 4),
                        SlotSymbol(":banana:", 5),
                        SlotSymbol(":grapes:", 6),
                    ],
                    [0.3, 0.2, 0.2, 0.15, 0.15],
                )
                for _ in range(3)
            ]
        )

    def pull_lever(self) -> list[SlotSymbol]:
        return [wheel.spin() for wheel in self.wheels]

    @property
    def num_wheels(self) -> int:
        return len(self.wheels)

    @property
    def prob_of_winning(self) -> float:
        return sum(
            wheel.get_probability(symbol) ** self.num_wheels
            for wheel in self.wheels
            for symbol in wheel.symbols
        )

    @property
    def rtp(self) -> float:
        average_winning = sum(
            symbol.value for wheel in self.wheels for symbol in wheel.symbols
        ) / len(self.wheels)
        average_bet = 1
        return (average_winning * self.prob_of_winning) / average_bet

    def get_winnings(self, *symbols: SlotSymbol, bet: int) -> int:
        return (sum(symbol.value for symbol in symbols) * bet) / self.prob_of_winning

