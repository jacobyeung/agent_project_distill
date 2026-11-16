import numpy as np
import pytest

from geo_bakeoff.contract import (
    FIELDS, camera_arrays, make_export, sample_grid, load_export, validate_export,
    validate_frames, write_export, raster_depth,
)


def fixture(n=64):
    cameras = np.repeat(np.eye(4)[None], n, axis=0)
    cameras[:, 0, 3] = np.arange(n) * 0.01
    intrinsics = np.repeat(np.array([[300., 0., 320.], [0., 300., 240.], [0., 0., 1.]])[None], n, axis=0)
    depth = np.full((n, 24, 32), 2., np.float32)
    frames = np.arange(n) * 3
    slots = np.arange(0, n, 2)
    return cameras, intrinsics, depth, frames, slots


def test_roundtrip(tmp_path):
    c, k, d, f, s = fixture()
    out = make_export(c, k, d, f, s, (480, 640), [0., -1., 0.])
    assert set(out) == FIELDS
    assert out["depth_grid"].shape == (32, 51, 51)
    validate_export(out, f[s])
    path = tmp_path / "clip.npz"
    write_export(path, out, check_disk=False)
    saved = load_export(path, f[s])
    for name in FIELDS:
        np.testing.assert_array_equal(saved[name], out[name])
    with pytest.raises(FileExistsError):
        write_export(path, out, check_disk=False)


def test_relative_cameras_are_world_gauge_invariant():
    c, k, d, f, s = fixture()
    a = make_export(c, k, d, f, s, (480, 640), [0., -1., 0.])
    gauge = np.array([[0., -1., 0., 2.], [1., 0., 0., 3.], [0., 0., 1., 4.], [0., 0., 0., 1.]])
    b = make_export(gauge @ c, k, d, f, s, (480, 640), [0., -1., 0.])
    for name in ("r_grav", "t_grav", "raw_pose"):
        np.testing.assert_allclose(a[name], b[name], atol=1e-12)


def test_frames_cannot_be_duplicated_or_fit_on_32():
    _, _, _, f, s = fixture()
    validate_frames(f, s, f[s])
    with pytest.raises(ValueError):
        validate_frames(f[:32], np.arange(32), f[:32])
    with pytest.raises(ValueError):
        validate_frames(np.repeat(f[:32], 2), s, f[s])
    with pytest.raises(ValueError):
        validate_frames(f, s, f[s] + 1)


def test_grid_endpoints_and_centres():
    d = np.broadcast_to(np.arange(8, dtype=np.float32) + .5, (1, 6, 8))
    grid = sample_grid(d, size=9)
    np.testing.assert_allclose(grid[0, 0], [.5, 1., 2., 3., 4., 5., 6., 7., 7.5])
    restored = raster_depth(np.full((2, 51, 51), 3., np.float32), (240, 320))
    np.testing.assert_array_equal(restored, 3.)


def test_raster_matches_frozen_normalized_coordinate_operation_order():
    grid = np.random.default_rng(0).normal(size=(2, 51, 51)).astype(np.float32)
    yy, xx = np.mgrid[:240, :320]
    x, y = (xx + .5) / 320 * 1000 * .05, (yy + .5) / 240 * 1000 * .05
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0+1, 50), np.minimum(y0+1, 50)
    fx, fy = x-x0, y-y0
    expected = (grid[:, y0, x0]*(1-fx)*(1-fy) + grid[:, y0, x1]*fx*(1-fy)
                + grid[:, y1, x0]*(1-fx)*fy + grid[:, y1, x1]*fx*fy).astype(np.float32)
    np.testing.assert_array_equal(raster_depth(grid), expected)


def test_invalid_geometry_and_unrepresentable_intrinsics():
    c, k, d, f, s = fixture()
    k[:, 0, 2] += 3
    with pytest.raises(ValueError, match="principal"):
        make_export(c, k, d, f, s, (480, 640), [0., -1., 0.])
    k[:, 0, 2] -= 3
    out = make_export(c, k, d, f, s, (480, 640), [0., -1., 0.])
    out["r_grav"][0, 0, 0] = 2.
    with pytest.raises(ValueError):
        validate_export(out)


def test_explicit_centre_projection_preserves_native_calibration():
    from geo_bakeoff.contract import centre_projection
    c, k, d, f, s = fixture()
    k[:, 0, 2] -= 13
    k[:, 1, 2] += 16
    projected, receipt = centre_projection(k, (480, 640))
    np.testing.assert_allclose(k[:, 0, 2], 307)
    np.testing.assert_allclose(projected[:, :2, 2], np.tile([320., 240.], (64, 1)))
    assert receipt["approximation"] is True
    assert receipt["max_principal_offset_px"] == 16
    make_export(c, projected, d, f, s, (480, 640), [0., -1., 0.])


def test_current_tower_loader_format():
    from geo_bakeoff.paths import mapped
    path = "/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_vcd/scannet__scene0011_00.npz"
    current = load_export(mapped(path))
    c, k = camera_arrays(current)
    assert c.shape == (32, 4, 4)
    assert k.shape == (32, 3, 3)
    np.testing.assert_allclose(c[:, :3, 3], current["t_grav"])
