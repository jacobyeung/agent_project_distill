import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pose_count import window_nested

def test_window_rule_nests_and_stays_inside():
    idx = list(range(100, 100 + 32 * 9, 9))
    a = window_nested(idx, 64)
    assert len(a) == 64 and set(idx) <= set(a) and a[0] == 100 and a[-1] == idx[-1]

def test_store_snapped_uses_only_available_and_fails_when_short():
    idx = list(range(0, 320, 10))
    avail = set(range(0, 320, 2))
    b = window_nested(idx, 64, avail)
    assert b is not None and set(b) <= avail | set(idx)
    assert window_nested(idx, 64, set(idx)) is None
    assert window_nested(list(range(32)), 64) is None
