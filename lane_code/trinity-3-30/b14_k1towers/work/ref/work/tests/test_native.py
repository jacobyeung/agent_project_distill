from types import SimpleNamespace

import numpy as np
import pytest

from geo_bakeoff.native import load_native, native_preflight, resample, write_native, verified_native


def test_native_resampling_keeps_pixel_centres():
    value = np.arange(24, dtype=np.float32).reshape(1, 4, 6)
    np.testing.assert_array_equal(resample(value, (4, 6)), value)
    np.testing.assert_allclose(resample(np.ones((2, 4, 6)), (8, 12)), 1.)


def test_cpu_cannot_admit_a_multiclip_native_export(tmp_path):
    with pytest.raises(PermissionError):
        native_preflight(tmp_path, 2, "cpu")


def test_native_archive_preserves_calibration_and_exact_anchors(tmp_path, monkeypatch):
    import geo_bakeoff.native as native
    monkeypatch.setattr(native, "check_space", lambda required=0: 10**12)
    frames, slots = np.arange(64) * 5, np.arange(0, 64, 2)
    k = np.repeat(np.array([[300., 0, 307.], [0, 300., 256.], [0, 0, 1.]])[None], 64, 0)
    prediction = SimpleNamespace(depth=np.full((64, 4, 6), 2.1234, np.float32), intrinsics=k, source_hw=(480, 640))
    receipt = write_native(tmp_path, "synthetic", "scene0011_00", prediction, frames, slots, "cpu")
    loaded = load_native(tmp_path / receipt["file"], frames[slots])
    verified_native(tmp_path, receipt, frames[slots])
    with pytest.raises(ValueError):
        verified_native(tmp_path, {**receipt, "sha256": "0"*64}, frames[slots])
    assert loaded["depth"].dtype == np.float16
    np.testing.assert_array_equal(loaded["intrinsics"], k[slots])
    with pytest.raises(AssertionError):
        load_native(tmp_path / receipt["file"], frames[slots] + 1)
    second = write_native(tmp_path, "synthetic", "scene0011_00", prediction, frames, slots, "cpu", run_id="run2")
    assert second["file"] != receipt["file"] and second["file"].startswith("run2/")
    verified_native(tmp_path, second, frames[slots])
    with (tmp_path / receipt["file"]).open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(ValueError):
        verified_native(tmp_path, receipt, frames[slots])
