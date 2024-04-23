from cogs.games.slots import AnyPayRule, Reelstrip, Symbol


def test_reelstrip_initialization_and_spinning(symbol_a, symbol_b, flat_window):
    symbols = [symbol_a, symbol_b]
    counts = [1, 3]
    reel = Reelstrip(symbols, counts)
    assert len(reel._build_wheel(symbols, counts)) == 4

    spin_result = reel.spin(flat_window)
    assert isinstance(spin_result[0], Symbol)


def test_reelstrip_str(symbol_a, symbol_b):
    symbols = [symbol_a, symbol_b]
    counts = [1, 3]
    reel = Reelstrip(symbols, counts)
    expected_str = "{'A': 1, 'B': 3}"
    assert str(reel) == expected_str


def test_build_wheel(symbol_a, symbol_b):
    symbols = [symbol_a, symbol_b, Symbol("C")]
    counts = [1, 2, 3]
    reel = Reelstrip(symbols, counts)
    wheel = reel._build_wheel(symbols, counts)
    assert len(wheel) == 6
    assert wheel.count(Symbol("A")) == 1
    assert wheel.count(Symbol("B")) == 2
    assert wheel.count(Symbol("C")) == 3


def test_anypayrule_generate_symbol_patterns(symbol_a, symbol_b, any_symbol):
    symbol_pattern = [symbol_a, any_symbol, symbol_b]
    any_payrule = AnyPayRule(symbol_pattern, 1000)
    expected_symbol_patterns = [
        [symbol_a, symbol_a, symbol_b],
        [symbol_a, symbol_b, symbol_b],
    ]
    assert all(
        pattern in expected_symbol_patterns for pattern in any_payrule.symbol_patterns
    )


def test_anypayrule(symbol_a, symbol_b, any_symbol):
    symbol_pattern = [symbol_a, any_symbol, symbol_b]
    any_payrule = AnyPayRule(symbol_pattern, 1000)
    assert repr(any_payrule) == "AnyPayRule([Symbol(A), AnySymbol(), Symbol(B)], 1000)"
    assert len(any_payrule.symbol_patterns) == 2


def test_scatter_payrule(payrule_scatter_symbol):
    assert (
        repr(payrule_scatter_symbol)
        == "ScatterPayRule([ScatterSymbol(A), ScatterSymbol(A), ScatterSymbol(A)], min_count=3, payout=1000)"
    )
    assert (
        str(payrule_scatter_symbol)
        == "ScatterPayRule([A.s, A.s, A.s], min_count=3, payout=1000)"
    )
    assert payrule_scatter_symbol == payrule_scatter_symbol
    assert payrule_scatter_symbol != 1000
