import pytest
from cogs.games.slots import (
    PayRule,
    GameBase,
    Reward,
    RewardType,
    Symbol,
    Reelstrip,
    Window,
    ScatterPayRule,
    AnySymbol,
    NotSymbol,
    ScatterSymbol,
    NotSymbol,
)


@pytest.fixture
def symbol_a():
    return Symbol("A")


@pytest.fixture
def symbol_b():
    return Symbol("B")


@pytest.fixture
def any_symbol():
    return AnySymbol()


@pytest.fixture
def not_symbol_a(symbol_a):
    return NotSymbol.from_symbol(symbol_a)


@pytest.fixture
def scatter_symbol(symbol_a):
    return ScatterSymbol.from_symbol(symbol_a)


@pytest.fixture
def basic_window():
    return Window([3] * 3)


@pytest.fixture
def flat_window():
    return Window([1] * 3)


@pytest.fixture
def fat_window():
    return Window([3] * 5)


@pytest.fixture
def basic_reelstrip(symbol_a, symbol_b):
    return Reelstrip([symbol_a, symbol_b], [1, 1])


@pytest.fixture
def basic_payrule(symbol_a):
    return PayRule([symbol_a] * 3, Reward(RewardType.MONEY, 1000))


@pytest.fixture
def basic_payrule_b(symbol_b):
    return PayRule([symbol_b] * 3, Reward(RewardType.MONEY, 500))


@pytest.fixture
def payrule_not_a(not_symbol_a):
    return PayRule([not_symbol_a] * 3, Reward(RewardType.MONEY, 1000))


@pytest.fixture
def payrule_any_symbol(any_symbol):
    return PayRule([any_symbol] * 3, Reward(RewardType.MONEY, 1000))


@pytest.fixture
def payrule_free_spin(symbol_a):
    return PayRule([symbol_a] * 3, Reward(RewardType.SPIN, 1))


@pytest.fixture
def payrule_scatter_symbol(scatter_symbol):
    return ScatterPayRule([scatter_symbol] * 3, 3, Reward(RewardType.MONEY, 1000))


@pytest.fixture
def basic_game(basic_window, basic_reelstrip, basic_payrule):
    return GameBase(
        "Test Game",
        [basic_window.topline()],
        [basic_payrule],
        [basic_reelstrip for _ in range(3)],
    )


@pytest.fixture
def free_spin_game(basic_window, basic_reelstrip, payrule_free_spin):
    return GameBase(
        "Free Spin Game",
        [basic_window.topline()],
        [payrule_free_spin],
        [basic_reelstrip for _ in range(3)],
    )


@pytest.fixture
def free_game(basic_window, basic_reelstrip, basic_payrule):
    return GameBase(
        "Free Game",
        [basic_window.topline()],
        [basic_payrule],
        [basic_reelstrip for _ in range(3)],
        is_free_game=True,
    )
