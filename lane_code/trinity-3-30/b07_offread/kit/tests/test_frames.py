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


def test_d0_lineage_trained_layout_is_known():
    assert F.bind_frames(export='done')['layout_override_reason'] is None
    with pytest.raises(F.FrameError):
        F.bind_frames(64, 'spread', export='done')


def test_caller_cannot_supply_a_trained_layout():
    with pytest.raises(TypeError):
        F.bind_frames(64, 'spread', export='step544', export_layout=dict(count=64, layout='spread'))


def test_unknown_export_layout_refused():
    with pytest.raises(F.FrameError):
        F.bind_frames(export='other')


@pytest.mark.parametrize('count,layout', [(64, 'duplicate'), (48, 'spread'), (32, 'P0.5')])
def test_layout_outside_evaluator_refused(count, layout):
    with pytest.raises(F.FrameError):
        F.bind_frames(count, layout, override_reason='x')


def test_blank_override_reason_does_not_admit_a_mismatch():
    with pytest.raises(F.FrameError):
        F.bind_frames(64, 'spread', override_reason='   ')
