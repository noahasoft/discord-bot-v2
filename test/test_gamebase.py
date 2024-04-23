from cogs.games.slots import (
    GameBase,
)


def test_gamebase_initialization(basic_window, basic_reelstrip, basic_payrule):
    game = GameBase(
        "Test Game",
        [basic_window.tl_diag()],
        [basic_payrule],
        [basic_reelstrip for _ in range(3)],
    )
    assert game.name == "Test Game"
    assert len(game.paylines) == 1
    assert len(game.pay_rules) == 1
    assert len(game.reels) == 3
