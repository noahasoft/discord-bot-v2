import pytest
from cogs.games.slots import (
    GameBase,
    Machine,
    Reelstrip,
    PayRule,
    Payline,
    Symbol,
    Window,
)


@pytest.mark.parametrize("rows, cols", [(3, 5), (1, 3)])
def test_window_initialization(rows, cols):
    window = Window([rows] * cols)
    assert window.rows_per_column == [rows] * cols
    assert window.cols == cols


def test_machine_initialization(basic_game, basic_window):
    games = [basic_game]
    machine = Machine(games, basic_window)
    assert machine.current_game_idx == 0


def test_machine_lever_pull(symbol_a, basic_payrule, flat_window):
    games = [
        GameBase(
            "Game1",
            [flat_window.topline()],
            [basic_payrule],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        )
    ]
    machine = Machine(games, flat_window)
    result = machine.pull_lever()
    assert len(result) == 3
    assert all(symbol.name == "A" for row in result for symbol in row)


def test_machine_evaluate_win(symbol_a, basic_payrule, flat_window):
    games = [
        GameBase(
            "Game1",
            [flat_window.topline()],
            [basic_payrule],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        )
    ]
    machine = Machine(games, flat_window)
    result = [[symbol_a] for _ in range(3)]
    winnings = machine.evaluate(result)
    assert winnings == 1000


def test_machine_no_win(symbol_b, basic_reelstrip, basic_payrule, flat_window):
    games = [
        GameBase(
            "Game1",
            [flat_window.topline()],
            [basic_payrule],
            [basic_reelstrip for _ in range(3)],
        )
    ]
    machine = Machine(games, flat_window)
    result = [[symbol_b], [symbol_b], [symbol_b]]
    winnings = machine.evaluate(result)
    assert winnings == 0


def test_validate_game_window_valid(symbol_a, symbol_b, fat_window):
    game = GameBase(
        "Test Game",
        [Payline([0, 1, 2])],
        [PayRule([symbol_a] * 3, 100.0)],
        [Reelstrip([symbol_a, symbol_b], [1, 9]) for _ in range(5)],
    )
    Machine.validate_game_window(fat_window, game)  # No exception should be raised


def test_validate_game_window_invalid_reels(symbol_a, symbol_b, fat_window):
    game = GameBase(
        "Test Game",
        [Payline([0, 1, 2])],
        [PayRule([symbol_a] * 3, 100.0)],
        [Reelstrip([symbol_a, symbol_b], [1, 9]) for _ in range(3)],
    )
    with pytest.raises(ValueError):
        Machine.validate_game_window(fat_window, game)


def test_validate_game_window_invalid_payline_index(symbol_a, symbol_b, fat_window):
    game = GameBase(
        "Test Game",
        [Payline([0, 1, 2, 3])],
        [PayRule([symbol_a] * 3, 100.0)],
        [Reelstrip([symbol_a, symbol_b], [1, 9]) for _ in range(5)],
    )
    with pytest.raises(ValueError):
        Machine.validate_game_window(fat_window, game)


def test_evaluate_multiple_paylines(
    symbol_a, symbol_b, basic_window, basic_payrule, basic_payrule_b
):
    games = [
        GameBase(
            "Game1",
            [basic_window.tl_diag(), basic_window.topline()],
            [basic_payrule, basic_payrule_b],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, basic_window)
    result = [
        [symbol_a, symbol_b, symbol_b],  # axx
        [symbol_b, symbol_a, symbol_b],  # xax
        [symbol_b, symbol_b, symbol_a],  # xxa
    ]
    winnings = machine.evaluate(result)
    assert winnings == 1000

    result = [
        [symbol_b, symbol_b, symbol_b],  # bbb
        [symbol_b, symbol_a, symbol_b],  # bxb
        [symbol_b, symbol_b, symbol_a],  # bbx
    ]
    winnings = machine.evaluate(result)
    assert winnings == 500


def test_machine_init_with_valid_games(symbol_a, basic_window, basic_reelstrip):
    games = [
        GameBase(
            "Game1",
            [Payline([0])],
            [PayRule(1, 50)],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        ),
        GameBase(
            "Game2",
            [Payline([0, 1])],
            [PayRule([symbol_a] * 2, 100)],
            [basic_reelstrip for _ in range(3)],
        ),
    ]
    machine = Machine(games, basic_window)
    assert len(machine.games) == 2
    assert machine.window == basic_window
    assert machine.current_game_idx == 0


def test_machine_init_with_empty_games(basic_window):
    with pytest.raises(ValueError):
        Machine([], basic_window)


def test_machine_init_with_invalid_window(symbol_a, fat_window):
    games = [
        GameBase(
            "Game1",
            [Payline([0])],
            [PayRule([symbol_a], 50)],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        )
    ]
    with pytest.raises(ValueError):
        Machine(games, fat_window)


def test_machine_pull_lever(
    symbol_a, symbol_b, basic_payrule, basic_payrule_b, flat_window
):
    games = [
        GameBase(
            "Game1",
            [flat_window.topline()],
            [basic_payrule],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        ),
        GameBase(
            "Game2",
            [flat_window.topline()],
            [basic_payrule_b],
            [Reelstrip([symbol_b], [1]) for _ in range(3)],
        ),
    ]
    machine = Machine(games, flat_window)
    result = machine.pull_lever()
    assert len(result) == 3
    assert all(isinstance(row[0], Symbol) for row in result)


def test_machine_evaluate_with_winning_result(
    symbol_a, symbol_b, basic_payrule, basic_payrule_b, flat_window
):
    games = [
        GameBase(
            "Game1",
            [flat_window.topline()],
            [basic_payrule],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        ),
        GameBase(
            "Game2",
            [flat_window.topline()],
            [basic_payrule_b],
            [Reelstrip([symbol_b], [1]) for _ in range(3)],
        ),
    ]
    machine = Machine(games, flat_window)
    result = [[symbol_a], [symbol_a], [symbol_a]]
    winnings = machine.evaluate(result)
    assert winnings == 1000


def test_machine_evaluate_with_no_win(
    symbol_b, basic_payrule, basic_payrule_b, flat_window, basic_reelstrip
):
    games = [
        GameBase(
            "Game1",
            [flat_window.topline()],
            [basic_payrule],
            [basic_reelstrip for _ in range(3)],
        ),
        GameBase(
            "Game2",
            [flat_window.topline()],
            [basic_payrule_b],
            [Reelstrip([symbol_b], [1]) for _ in range(3)],
        ),
    ]
    machine = Machine(games, flat_window)
    result = [[symbol_b], [symbol_b], [symbol_b]]
    winnings = machine.evaluate(result)
    assert winnings == 0


def test_machine_is_on_scoreline(
    symbol_a, symbol_b, basic_window, basic_payrule, basic_payrule_b
):
    games = [
        GameBase(
            "Game1",
            [basic_window.tl_diag(), basic_window.topline()],
            [basic_payrule, basic_payrule_b],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, basic_window)
    assert machine.is_on_scoreline(0, 0) == True
    assert machine.is_on_scoreline(1, 1) == True
    assert machine.is_on_scoreline(2, 2) == True
    assert machine.is_on_scoreline(1, 0) == True
    assert machine.is_on_scoreline(2, 0) == True


def test_machine_prob_winning(
    symbol_a, symbol_b, basic_window, basic_payrule, basic_payrule_b
):
    games = [
        GameBase(
            "Game1",
            [basic_window.tl_diag(), basic_window.topline()],
            [basic_payrule, basic_payrule_b],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, basic_window)
    assert machine.prob_winning(basic_payrule) == 0.125
    assert machine.prob_winning(basic_payrule_b) == 0.125


def test_machine_hit_rate(
    symbol_a, symbol_b, basic_window, basic_payrule, basic_payrule_b
):
    games = [
        GameBase(
            "Game1",
            [basic_window.tl_diag(), basic_window.topline()],
            [basic_payrule, basic_payrule_b],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, basic_window)
    assert machine.hit_rate(basic_payrule) == 8.0
    assert machine.hit_rate(basic_payrule_b) == 8.0


def test_machine_hit_frequency(
    symbol_a, symbol_b, basic_window, basic_payrule, basic_payrule_b
):
    games = [
        GameBase(
            "Game1",
            [basic_window.tl_diag(), basic_window.topline()],
            [basic_payrule, basic_payrule_b],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, basic_window)
    assert machine.hit_frequency(basic_payrule) == 0.125
    assert machine.hit_frequency(basic_payrule_b) == 0.125


def test_machine_total_prob_winning(
    symbol_a, symbol_b, basic_window, basic_payrule, basic_payrule_b
):
    games = [
        GameBase(
            "Game1",
            [basic_window.tl_diag(), basic_window.topline()],
            [basic_payrule, basic_payrule_b],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, basic_window)
    assert machine.total_prob_winning == 0.25


def test_machine_rtp(symbol_a, symbol_b, basic_window, basic_payrule, basic_payrule_b):

    games = [
        GameBase(
            "Game1",
            [basic_window.tl_diag(), basic_window.topline()],
            [basic_payrule, basic_payrule_b],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, basic_window)
    assert machine.rtp(1.0) == 375


def test_machine_volatility(
    symbol_a, symbol_b, basic_window, basic_payrule, basic_payrule_b
):

    games = [
        GameBase(
            "Game1",
            [basic_window.tl_diag(), basic_window.topline()],
            [basic_payrule, basic_payrule_b],
            [Reelstrip([symbol_a, symbol_b], [3, 3]) for _ in range(3)],
        )
    ]
    machine = Machine(games, basic_window)

    assert machine.volatility == pytest.approx(0.002667)


@pytest.mark.parametrize("game_count", [1, 2])
def test_machine_init_with_multiple_games(symbol_a, basic_window, game_count):
    games = [
        GameBase(
            f"Game{i+1}",
            [Payline([0])],
            [PayRule([symbol_a], 50)],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        )
        for i in range(game_count)
    ]
    machine = Machine(games, basic_window)
    assert len(machine.games) == game_count


def test_not_rule(symbol_a, symbol_b, basic_reelstrip, flat_window):
    games = [
        GameBase(
            "Game1",
            [Payline([0, 0, 0])],
            [PayRule([symbol_a, symbol_a], 1000)],
            [basic_reelstrip for _ in range(3)],
        )
    ]
    machine = Machine(games, flat_window)
    result = [[symbol_a], [symbol_a], [symbol_b]]
    winnings = machine.evaluate(result)
    assert winnings == 1000


@pytest.mark.parametrize("invalid_count", [0, 2])
def test_validate_game_window(symbol_a, invalid_count, basic_window, basic_reelstrip):
    game = GameBase(
        "Test Game",
        [Payline([0, 1, 2])],
        [PayRule([symbol_a] * 3, 1000)],
        [basic_reelstrip for _ in range(invalid_count)],
    )
    with pytest.raises(ValueError):
        Machine.validate_game_window(basic_window, game)


def test_machine_lever_pull_and_evaluate_win(basic_game, basic_window):
    machine = Machine([basic_game], basic_window)
    result = machine.pull_lever()
    winnings = machine.evaluate(result)
    assert isinstance(result, list) and isinstance(winnings, (int, float))


def test_not_payrule(payrule_not_a, symbol_a, symbol_b, flat_window):
    games = [
        GameBase(
            "Game1",
            [flat_window.topline()],
            [payrule_not_a],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        ),
    ]
    machine = Machine(games, flat_window)
    result = [[symbol_b], [symbol_b], [symbol_b]]
    winnings = machine.evaluate(result)
    assert winnings == 1000
    result = [[symbol_a], [symbol_a], [symbol_a]]
    winnings = machine.evaluate(result)
    assert winnings == 0


def test_any_symbol_payrule(payrule_any_symbol, symbol_a, symbol_b, flat_window):
    games = [
        GameBase(
            "Game1",
            [flat_window.topline()],
            [payrule_any_symbol],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        ),
    ]
    machine = Machine(games, flat_window)
    result = [[symbol_b], [symbol_b], [symbol_b]]
    winnings = machine.evaluate(result)
    assert winnings == 1000
    result = [[symbol_a], [symbol_a], [symbol_a]]
    winnings = machine.evaluate(result)
    assert winnings == 1000


def test_run_scatter_payrule(symbol_a, symbol_b, payrule_scatter_symbol, basic_window):
    games = [
        GameBase(
            "Game1",
            [basic_window.centerline()],
            [payrule_scatter_symbol],
            [Reelstrip([symbol_a], [1]) for _ in range(3)],
        ),
    ]
    machine = Machine(games, basic_window)
    result = [
        [symbol_b, symbol_a, symbol_b],
        [symbol_a, symbol_b, symbol_b],
        [symbol_b, symbol_b, symbol_a],
    ]
    winnings = machine.evaluate(result)
    assert winnings == 1000
