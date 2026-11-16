import numpy as np
import pytest

from geo_bakeoff.hybrids import clip_ratio, fit_affine, blend_depth, hybrid
from test_contract import fixture
from geo_bakeoff.contract import make_export, validate_export


def test_clip_scale_and_affine_recover_known_values():
    x = np.linspace(.3, 6, 64 * 51 * 51).reshape(64, 51, 51).astype(np.float32)
    assert clip_ratio(x, 1.3 * x) == pytest.approx(1.3)
    a, b = fit_affine(x, 1.2 * x + .15)
    np.testing.assert_allclose(a, 1.2, atol=1e-5)
    np.testing.assert_allclose(b, .15, atol=1e-5)


def test_ratio_never_uses_missing_values():
    x = np.ones((2, 51, 51), np.float32)
    y = 2 * x
    y[:, :5] = 0
    assert clip_ratio(x, y) == pytest.approx(2)
    with pytest.raises(ValueError):
        clip_ratio(x, np.zeros_like(x))


def test_ensemble_requires_both_valid_sources():
    x = np.array([1., 0., 2.])
    y = np.array([3., 4., 0.])
    np.testing.assert_array_equal(blend_depth(x, y), [2., 0., 0.])


def test_scale_hybrid_scales_translation_with_depth():
    c, k, d, f, s = fixture()
    base = make_export(c, k, d, f, s, (480, 640), [0., -1., 0.])
    candidate = {key: value.copy() for key, value in base.items()}
    candidate["depth_grid"] *= 1.5
    out, meta = hybrid("clip_scale", base, candidate)
    np.testing.assert_allclose(out["depth_grid"], base["depth_grid"] * 1.5)
    np.testing.assert_allclose(out["t_grav"], base["t_grav"] * 1.5)
    np.testing.assert_allclose(out["raw_pose"][:, :3], base["raw_pose"][:, :3] * 1.5)
    validate_export(out)
    assert meta["pose_scale_applied"]


def test_depth_swap_keeps_pose_and_intrinsics():
    c, k, d, f, s = fixture()
    base = make_export(c, k, d, f, s, (480, 640), [0., -1., 0.])
    other = {key: value.copy() for key, value in base.items()}
    other["depth_grid"] *= 2
    out, _ = hybrid("depth", base, other)
    for key in ("r_grav", "t_grav", "fov_hw"):
        np.testing.assert_array_equal(out[key], base[key])
    other["anchor_frame_indices"][0] += 1
    with pytest.raises(ValueError):
        hybrid("depth", base, other)


def test_pose_counterfactual_holds_candidate_depth_and_calibration_fixed():
    c, k, d, f, s = fixture()
    base = make_export(c, k, d, f, s, (480, 640), [0., -1., 0.])
    changed_k = k.copy()
    changed_k[:, 0, 0] *= 1.2
    candidate = make_export(c, changed_k, d*1.1, f, s, (480, 640), [0., -1., 0.])
    result, _ = hybrid("pose_g3t", base, candidate)
    validate_export(result)
    for key in ("r_grav", "t_grav"):
        np.testing.assert_array_equal(result[key], base[key])
    for key in ("depth_grid", "fov_hw"):
        np.testing.assert_array_equal(result[key], candidate[key])
