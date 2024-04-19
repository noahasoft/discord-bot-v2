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
    assert len(reel._build_wheel(symbols, counts)) == 4  # Simple count check

    window = Window(1, 3)
    spin_result = reel.spin(window)
    assert len(spin_result) == 1
    assert isinstance(spin_result[0], Symbol)


def test_gamebase_initialization():
    game = GameBase(
        "Test Game",
        [Window(3, 3).tl_diag()],
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
    window = Window(1, 3)
    games = [
        GameBase(
            "Game1",
            [window.topline()],
            [PayRule(3, 1000, symbol_a)],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        )
    ]
    machine = Machine(games, window)
    result = machine.pull_lever()
    assert len(result) == 3
    assert all(symbol.name == "A" for row in result for symbol in row)


def test_machine_evaluate_win():
    symbol_a = Symbol("A")
    window = Window(1, 3)
    games = [
        GameBase(
            "Game1",
            [window.topline()],
            [PayRule(3, 1000, symbol_a)],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        )
    ]
    machine = Machine(games, window)
    result = [[symbol_a] for _ in range(3)]
    winnings = machine.evaluate(result)
    assert winnings == 1000


def test_machine_no_win():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(1, 3)
    games = [
        GameBase(
            "Game1",
            [window.topline()],
            [PayRule(3, 1000, symbol_a)],
            [Reelstrip([symbol_a, symbol_b], [1, 1]) for _ in range(3)],
        )
    ]
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
    window = Window(3, 3)
    games = [
        GameBase(
            "Game1",
            [window.tl_diag(), window.topline()],
            [PayRule(3, 1000, symbol_a), PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
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


def test_build_wheel():
    symbols = [Symbol("A"), Symbol("B"), Symbol("C")]
    counts = [1, 2, 3]
    reel = Reelstrip(symbols, counts)
    wheel = reel._build_wheel(symbols, counts)
    assert len(wheel) == 6
    assert wheel.count(Symbol("A")) == 1
    assert wheel.count(Symbol("B")) == 2
    assert wheel.count(Symbol("C")) == 3


def test_machine_init_with_valid_games():
    games = [
        GameBase(
            "Game1",
            [Payline([0])],
            [PayRule(1, 50)],
            [Reelstrip([Symbol("A")], [1]) for _ in range(3)],
        ),
        GameBase(
            "Game2",
            [Payline([0, 1])],
            [PayRule(2, 100)],
            [Reelstrip([Symbol("A"), Symbol("B")], [1, 1]) for _ in range(3)],
        ),
    ]
    window = Window(3, 3)
    machine = Machine(games, window)
    assert len(machine.games) == 2
    assert machine.window == window
    assert machine.current_game_idx == 0


def test_machine_init_with_empty_games():
    with pytest.raises(ValueError):
        Machine([], Window(3, 3))


def test_machine_init_with_invalid_window():
    games = [
        GameBase(
            "Game1",
            [Payline([0])],
            [PayRule(1, 50)],
            [Reelstrip([Symbol("A")], [1]) for _ in range(3)],
        )
    ]
    window = Window(3, 5)
    with pytest.raises(ValueError):
        Machine(games, window)


def test_machine_pull_lever():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(1, 3)
    games = [
        GameBase(
            "Game1",
            [window.topline()],
            [PayRule(3, 1000, symbol_a)],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        ),
        GameBase(
            "Game2",
            [window.topline()],
            [PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_b], [1]) for _ in range(3)],
        ),
    ]
    machine = Machine(games, window)
    result = machine.pull_lever()
    assert len(result) == 3
    assert all(isinstance(row[0], Symbol) for row in result)


def test_machine_evaluate_with_winning_result():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(1, 3)
    games = [
        GameBase(
            "Game1",
            [window.topline()],
            [PayRule(3, 1000, symbol_a)],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        ),
        GameBase(
            "Game2",
            [window.topline()],
            [PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_b], [1]) for _ in range(3)],
        ),
    ]
    machine = Machine(games, window)
    result = [[symbol_a], [symbol_a], [symbol_a]]
    winnings = machine.evaluate(result)
    assert winnings == 1000


def test_machine_evaluate_with_no_win():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(1, 3)
    games = [
        GameBase(
            "Game1",
            [window.topline()],
            [PayRule(3, 1000, symbol_a)],
            [Reelstrip([symbol_a, symbol_b], [1, 1]) for _ in range(3)],
        ),
        GameBase(
            "Game2",
            [window.topline()],
            [PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_b], [1]) for _ in range(3)],
        ),
    ]
    machine = Machine(games, window)
    result = [[symbol_b], [symbol_b], [symbol_b]]
    winnings = machine.evaluate(result)
    assert winnings == 0


def test_machine_is_on_scoreline():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(3, 3)
    games = [
        GameBase(
            "Game1",
            [window.tl_diag(), window.topline()],
            [PayRule(3, 1000, symbol_a), PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, window)
    assert machine.is_on_scoreline(0, 0) == True
    assert machine.is_on_scoreline(1, 1) == True
    assert machine.is_on_scoreline(2, 2) == True
    assert machine.is_on_scoreline(1, 0) == True
    assert machine.is_on_scoreline(2, 0) == True


def test_machine_prob_winning():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(3, 3)
    games = [
        GameBase(
            "Game1",
            [window.tl_diag(), window.topline()],
            [PayRule(3, 1000, symbol_a), PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, window)
    assert machine.prob_winning(PayRule(3, 1000, symbol_a)) == 0.125
    assert machine.prob_winning(PayRule(3, 500, symbol_b)) == 0.125


def test_machine_hit_rate():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(3, 3)
    games = [
        GameBase(
            "Game1",
            [window.tl_diag(), window.topline()],
            [PayRule(3, 1000, symbol_a), PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, window)
    assert machine.hit_rate(PayRule(3, 1000, symbol_a)) == 8.0
    assert machine.hit_rate(PayRule(3, 500, symbol_b)) == 8.0


def test_machine_hit_frequency():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(3, 3)
    games = [
        GameBase(
            "Game1",
            [window.tl_diag(), window.topline()],
            [PayRule(3, 1000, symbol_a), PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, window)
    assert machine.hit_frequency(PayRule(3, 1000, symbol_a)) == 0.125
    assert machine.hit_frequency(PayRule(3, 500, symbol_b)) == 0.125


def test_machine_total_prob_winning():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(3, 3)
    games = [
        GameBase(
            "Game1",
            [window.tl_diag(), window.topline()],
            [PayRule(3, 1000, symbol_a), PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, window)
    assert machine.total_prob_winning == 0.25


def test_machine_rtp():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(3, 3)
    games = [
        GameBase(
            "Game1",
            [window.tl_diag(), window.topline()],
            [PayRule(3, 1000, symbol_a), PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, window)
    assert machine.rtp(1.0) == 375


def test_machine_volatility():
    symbol_a = Symbol("A")
    symbol_b = Symbol("B")
    window = Window(3, 3)
    games = [
        GameBase(
            "Game1",
            [window.tl_diag(), window.topline()],
            [PayRule(3, 1000, symbol_a), PayRule(3, 500, symbol_b)],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, window)

    assert machine.volatility == pytest.approx(0.002667)
