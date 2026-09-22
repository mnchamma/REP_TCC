from load_tests.analyze import percentile


def test_tail_percentiles_are_not_means():
    values = [10] * 90 + [100] * 5 + [1000] * 4 + [30000]
    assert percentile(values, .90) == 10
    assert percentile(values, .95) == 100
    assert percentile(values, .99) == 1000
    assert percentile(values, 1) == 30000
    assert percentile([], .99) is None
