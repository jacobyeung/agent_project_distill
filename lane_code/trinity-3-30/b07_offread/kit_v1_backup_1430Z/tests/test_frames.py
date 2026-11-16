import pytest

from offkit import frames as F


def test_default_matches_step544_training():
    f = F.bind_frames()
    assert (f['count'], f['layout'], f['processor_frames'], f['temporal_groups']) == (32, 'duplicate', 64, 32)
    assert f['layout_override_reason'] is None


def test_64_spread_on_step544_refused_without_override():
    with pytest.raises(F.FrameError):
        F.bind_frames(64, 'spread')
    f = F.bind_frames(64, 'spread', override_reason='layout probe')
    assert f['layout_override_reason'] == 'layout probe' and f['temporal_groups'] == 32


def test_64_export_binds_its_own_layout():
    f = F.bind_frames(64, 'spread', export='done:x', export_layout=dict(count=64, layout='spread'))
    assert f['layout_override_reason'] is None


def test_unknown_export_layout_refused():
    with pytest.raises(F.FrameError):
        F.bind_frames(export='done:x')


@pytest.mark.parametrize('count,layout', [(64, 'duplicate'), (48, 'spread'), (32, 'P0.5')])
def test_layout_outside_evaluator_refused(count, layout):
    with pytest.raises(F.FrameError):
        F.bind_frames(count, layout, override_reason='x')
