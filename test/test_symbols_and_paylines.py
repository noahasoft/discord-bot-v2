import pytest
from cogs.games.slots import Payline


def test_symbol(symbol_a):
    assert symbol_a.name == "A"
    assert str(symbol_a) == "A"


def test_payline_access():
    payline = Payline([0, 1, 2])
    for i, idx in enumerate(payline):
        assert idx == i
    with pytest.raises(IndexError):
        _ = payline[i + 1]


def test_not_symbol_str(symbol_a, not_symbol_a):
    assert str(not_symbol_a) == "#A"
    assert repr(not_symbol_a) == "NotSymbol(A)"
    assert not_symbol_a != symbol_a


def test_any_symbol(any_symbol, symbol_a, symbol_b):
    assert str(any_symbol) == "*"
    assert repr(any_symbol) == "AnySymbol()"
    assert any_symbol == symbol_a
    assert any_symbol == symbol_b
    assert hash(any_symbol) == hash("Any")
