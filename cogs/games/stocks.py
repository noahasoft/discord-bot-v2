from dataclasses import dataclass
import datetime
import math
import random
from typing import Optional


def clamp(v, min, max):
    if v < min:
        return min
    elif v > max:
        return max
    else:
        return v


@dataclass
class GBMSystem:
    """
    Geometric Brownian Motion Parameters
    """

    mu: float = 0.1  # drift coefficient
    n: int = 100  # number of steps
    T: int = 1  # time in years
    S0: float = 100.0  # initial stock price
    sigma: float = 0.3  # volatility

    def __post_init__(self):
        if self.n == 0:
            raise ZeroDivisionError("n must be positive")
        if self.n < 0:
            raise ValueError("n must be non-negative")
        if self.T <= 0:
            raise ValueError("T must be positive")
        if self.n < 1:
            raise ValueError("n must be at least 1")
        if self.S0 <= 0:
            raise ValueError("S0 must be positive")
        self.current_price = self.S0
        self.current_step = 0
        self.dt = self.T / self.n  # time step size

    def get_next(self) -> float:
        """
        Generate the next stock price using GBM.
        """
        if self.current_step < self.n:
            normal_sample = random.gauss(0, math.sqrt(self.dt))
            value = (
                self.mu - self.sigma**2 / 2
            ) * self.dt + self.sigma * normal_sample
            self.current_price *= math.exp(value)
            self.current_step += 1
        return self.current_price


class Stock:
    def __init__(
        self,
        name: str,
        symbol: str,
        params: GBMSystem,
        date: Optional[str] = None,
        high: Optional[float] = None,
        low: Optional[float] = None,
    ):
        self.name = name
        self.params = params
        self.symbol = symbol
        self.high = high or params.S0
        self.low = low or params.S0
        self.date = date or datetime.datetime.now().strftime("%Y-%m-%d")

    def __str__(self) -> str:
        return f"{self.name}: {self.params.current_price}"

    @classmethod
    def from_row(cls, row) -> "Stock":
        # s.name, s.symbol, s.price, h.date, h.high, h.low
        return cls(row[0], row[1], GBMSystem(S0=row[2]), row[3], row[4], row[5])

    def get_next(self) -> float:
        return self.params.get_next()

    @property
    def price(self) -> float:
        return self.params.current_price


class Market:
    def __init__(self) -> None:
        self.stocks: dict[str, Stock] = {}

    @classmethod
    def init_from_stocks(cls, stocks: list[Stock]) -> "Market":
        market = cls()
        for stock in stocks:
            market.stocks[stock.symbol] = stock
        return market

    def get_stock(self, symbol: str) -> Stock:
        return self.stocks[symbol]

    def get_stock_price(self, symbol: str) -> float:
        return self.get_stock(symbol).price

    def get_stock_names(self) -> list[str]:
        return [stock.name for stock in self.stocks.values()]

    def get_stock_symbols(self) -> list[str]:
        return list(self.stocks.keys())
