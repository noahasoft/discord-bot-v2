import pytest
from cogs.games.slots import (
    PayRule,
    Payline,
    GameBase,
    Machine,
    Symbol,
    Reelstrip,
    Window,
)


def test_symbol():
    sym = Symbol("A")
    assert str(sym) == "A"
    assert hash(sym) == hash("A")


def test_payline_access():
    payline = Payline([0, 1, 2])
    for i, idx in enumerate(payline):
        assert idx == i
    with pytest.raises(IndexError):
        _ = payline[i + 1]


def test_window_initialization():
    r, c = 3, 5
    window = Window(r, c)
    assert window.rows == r
    assert window.cols == c


def test_reelstrip_initialization_and_spinning():
    symbols = [Symbol("A"), Symbol("B")]
    counts = [1, 3]
    reel = Reelstrip(symbols, counts)
    assert len(reel.build_wheel(symbols, counts)) == 4  # Simple count check

    window = Window(1, 3)
    spin_result = reel.spin(window)
    assert len(spin_result) == 1
    assert isinstance(spin_result[0], Symbol)


def test_gamebase_initialization():
    game = GameBase(
        "Test Game",
        [Payline([0, 1, 2])],
        [PayRule(3, 100.0)],
        [Reelstrip([Symbol("A"), Symbol("B")], [1, 9]) for _ in range(3)],
    )
    assert game.name == "Test Game"
    assert len(game.paylines) == 1
    assert len(game.pay_rules) == 1
    assert len(game.reels) == 3


def test_machine_initialization():
    games = [
        GameBase(
            "Game1",
            [Payline([0])],
            [PayRule(1, 50)],
            [Reelstrip([Symbol("A")], [1]) for _ in range(3)],
        )
    ]
    window = Window(3, 3)
    machine = Machine(games, window)
    assert machine.current_game_idx == 0


def test_machine_lever_pull():
    symbol_a = Symbol("A")
    games = [
        GameBase(
            "Game1",
            [Payline([0, 0, 0])],
            [PayRule(3, 1000, symbol_a)],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        )
    ]
    window = Window(1, 3)
    machine = Machine(games, window)
    result = machine.pull_lever()
    assert len(result) == 3
    assert all(symbol.name == "A" for row in result for symbol in row)


def test_machine_evaluate_win():
    symbol_a = Symbol("A")
    games = [
        GameBase(
            "Game1",
            [Payline([0, 0, 0])],
            [PayRule(3, 1000, symbol_a)],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        )
    ]
    window = Window(1, 3)
    machine = Machine(games, window)
    result = [[symbol_a] for _ in range(3)]
    winnings = machine.evaluate(result)
    assert winnings == 1000


def test_machine_no_win():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    games = [
        GameBase(
            "Game1",
            [Payline([0, 0, 0])],
            [PayRule(3, 1000, symbol_a)],
            [Reelstrip([symbol_a, symbol_b], [1, 1]) for _ in range(3)],
        )
    ]
    window = Window(1, 3)
    machine = Machine(games, window)
    result = [[symbol_b], [symbol_b], [symbol_b]]
    winnings = machine.evaluate(result)
    assert winnings == 0


def test_not_rule():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    games = [
        GameBase(
            "Game1",
            [Payline([0, 0, 0])],
            [PayRule(2, 1000, symbol_a)],
            [Reelstrip([symbol_a, symbol_b], [1, 1]) for _ in range(3)],
        )
    ]
    window = Window(1, 3)
    machine = Machine(games, window)
    result = [[symbol_a], [symbol_a], [symbol_b]]
    winnings = machine.evaluate(result)
    assert winnings == 1000


def test_validate_game_window_valid():
    window = Window(3, 5)
    game = GameBase(
        "Test Game",
        [Payline([0, 1, 2])],
        [PayRule(3, 100.0)],
        [Reelstrip([Symbol("A"), Symbol("B")], [1, 9]) for _ in range(5)],
    )
    Machine.validate_game_window(window, game)  # No exception should be raised


def test_validate_game_window_invalid_reels():
    window = Window(3, 5)
    game = GameBase(
        "Test Game",
        [Payline([0, 1, 2])],
        [PayRule(3, 100.0)],
        [Reelstrip([Symbol("A"), Symbol("B")], [1, 9]) for _ in range(3)],
    )
    with pytest.raises(ValueError):
        Machine.validate_game_window(window, game)


def test_validate_game_window_invalid_payline_index():
    window = Window(3, 5)
    game = GameBase(
        "Test Game",
        [Payline([0, 1, 2, 3])],
        [PayRule(3, 100.0)],
        [Reelstrip([Symbol("A"), Symbol("B")], [1, 9]) for _ in range(5)],
    )
    with pytest.raises(ValueError):
        Machine.validate_game_window(window, game)


def test_evaluate_multiple_paylines():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    games = [
        GameBase(
            "Game1",
            [Payline([0, 1, 2]), Payline([0, 0, 0])],
            [PayRule(3, 1000, symbol_a), PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    window = Window(3, 3)
    machine = Machine(games, window)
    result = [
        [symbol_a, symbol_b, symbol_b],
        [symbol_b, symbol_a, symbol_b],
        [symbol_b, symbol_b, symbol_a],
    ]
    winnings = machine.evaluate(result)
    assert winnings == 1000

    result = [
        [symbol_b, symbol_b, symbol_b],
        [symbol_b, symbol_a, symbol_b],
        [symbol_b, symbol_b, symbol_a],
    ]
    winnings = machine.evaluate(result)
    assert winnings == 500


def test_reelstrip_str():
    symbols = [Symbol("A"), Symbol("B")]
    counts = [1, 3]
    reel = Reelstrip(symbols, counts)
    expected_str = "{'A': 1, 'B': 3}"
    assert str(reel) == expected_str
