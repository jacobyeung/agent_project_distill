import pytest
from offkit.frames import bind_frames, FrameError

def test_default_and_spread_cost():
    a=bind_frames()
    b=bind_frames(64,'spread',override_reason='Explicit 64-frame diagnostic.')
    assert a['processor_frames']==b['processor_frames']==64
    assert a['temporal_groups']==b['temporal_groups']==32

@pytest.mark.parametrize('count,layout',[(64,'spread'),(32,'spread'),(64,'duplicate')])
def test_step544_guard(count,layout):
    with pytest.raises(FrameError):bind_frames(count,layout)

def test_done_layout_owned_by_offkit():
    assert bind_frames(export='done')['count']==32
    with pytest.raises(FrameError):bind_frames(64,'spread',export='done')
    assert bind_frames(64,'spread',export='done',override_reason='Explicit diagnostic')['count']==64
