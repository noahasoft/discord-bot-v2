import pytest
from cogs.games.roulette import BetType, Color, Bet, SpinResult, RouletteGame


@pytest.fixture
def roulette_game():
    return RouletteGame(seed=1)


def test_place_bet(roulette_game):
    bet = Bet(BetType.NUMBER, 5, 10.0)
    roulette_game.place_bet(bet)
    assert len(roulette_game.bets) == 1
    assert roulette_game.bets[0] == bet


def test_evaluate_bets_number_match(roulette_game):
    result = SpinResult(5, Color.RED)
    bet = Bet(BetType.NUMBER, 5, 10.0)
    roulette_game.place_bet(bet)
    payouts = roulette_game.evaluate_bets(result)
    assert len(payouts) == 1
    assert payouts[bet] == 350.0


def test_evaluate_bets_number_no_match(roulette_game):
    result = SpinResult(10, Color.BLACK)
    bet = Bet(BetType.NUMBER, 5, 10.0)
    roulette_game.place_bet(bet)
    payouts = roulette_game.evaluate_bets(result)
    assert len(payouts) == 1
    assert payouts[bet] == -10.0


def test_evaluate_bets_color_match(roulette_game):
    result = SpinResult(10, Color.RED)
    bet = Bet(BetType.COLOR, Color.RED, 10.0)
    roulette_game.place_bet(bet)
    payouts = roulette_game.evaluate_bets(result)
    assert len(payouts) == 1
    assert payouts[bet] == 20.0


def test_evaluate_bets_color_no_match(roulette_game):
    result = SpinResult(10, Color.BLACK)
    bet = Bet(BetType.COLOR, Color.RED, 10.0)
    roulette_game.place_bet(bet)
    payouts = roulette_game.evaluate_bets(result)
    assert len(payouts) == 1
    assert payouts[bet] == -10.0


def test_evaluate_bets_odd_even_match(roulette_game):
    result = SpinResult(5, Color.RED)
    bet = Bet(BetType.ODD_EVEN, "Odd", 10.0)
    roulette_game.place_bet(bet)
    payouts = roulette_game.evaluate_bets(result)
    assert len(payouts) == 1
    assert payouts[bet] == 20.0


def test_evaluate_bets_odd_even_no_match(roulette_game):
    result = SpinResult(10, Color.BLACK)
    bet = Bet(BetType.ODD_EVEN, "Odd", 10.0)
    roulette_game.place_bet(bet)
    payouts = roulette_game.evaluate_bets(result)
    assert len(payouts) == 1
    assert payouts[bet] == 0


def test_clear_bets(roulette_game):
    bet = Bet(BetType.NUMBER, 5, 10.0)
    roulette_game.place_bet(bet)
    roulette_game.clear_bets()
    assert len(roulette_game.bets) == 0


def test_even_odd_bets(roulette_game):
    result = SpinResult(5, Color.RED)
    even_bet = Bet(BetType.ODD_EVEN, "Even", 10.0)
    odd_bet = Bet(BetType.ODD_EVEN, "Odd", 10.0)
    roulette_game.place_bet(even_bet)
    roulette_game.place_bet(odd_bet)
    payouts = roulette_game.evaluate_bets(result)
    assert len(payouts) == 2
    assert payouts[even_bet] == 0
    assert payouts[odd_bet] == 20.0
