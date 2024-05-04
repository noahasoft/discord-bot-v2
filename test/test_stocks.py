import pytest
from cogs.games.stocks import GBMSystem, Stock


def test_get_next():
    params = GBMSystem()
    initial_price = params.current_price
    next_price = params.get_next()
    assert next_price != initial_price
    assert next_price == params.current_price


def test_post_init():
    params = GBMSystem()
    assert params.current_price == params.S0
    assert params.current_step == 0
    assert params.dt == params.T / params.n


def test_invalid_parameters():
    with pytest.raises(ZeroDivisionError):
        GBMSystem(n=0)
    with pytest.raises(ValueError):
        GBMSystem(T=-1)
    with pytest.raises(ValueError):
        GBMSystem(n=-1)


def test_stock():
    s = Stock("Apple", "AAPL", GBMSystem(S0=100.0))
    assert s.price == 100.0
    assert s.get_next() != 100.0
    assert s.high != None
    assert s.low != None