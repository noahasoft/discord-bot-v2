from dataclasses import dataclass
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
    def __init__(self, name: str, params: GBMSystem, symbol: Optional[str] = None):
        self.name = name
        self.symbol = symbol or name[:4].upper()
        self.params = params

    def __str__(self) -> str:
        return f"{self.name}: {self.params.current_price}"

    @classmethod
    def from_row(cls, row) -> "Stock":
        return cls(row[0], GBMSystem(S0=row[2]), row[1])

    def get_next(self) -> float:
        return self.params.get_next()

    @property
    def price(self) -> float:
        return self.params.current_price
