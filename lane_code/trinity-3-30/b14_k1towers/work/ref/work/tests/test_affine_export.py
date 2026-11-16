import numpy as np

from geo_bakeoff.contract import make_export, validate_export
from geo_bakeoff.hybrids import hybrid, fit_affine
from test_contract import fixture


def test_affine_hybrid_retains_float32_export_contract():
    cameras, intrinsics, depth, frames, slots = fixture()
    baseline = make_export(cameras, intrinsics, depth, frames, slots, (480, 640), [0., -1., 0.])
    candidate = {key: value.copy() for key, value in baseline.items()}
    candidate["depth_grid"] = candidate["depth_grid"] * np.float32(1.2) + np.float32(.15)
    result, _ = hybrid("frame_affine", baseline, candidate)
    validate_export(result)
    assert result["depth_grid"].dtype == np.float32


def test_negative_affine_slope_uses_reported_positive_scale_fallback():
    source = np.linspace(1., 2., 200).reshape(1, 10, 20)
    target = 3. - source
    scales, shifts, report = fit_affine(source, target, diagnostics=True)
    np.testing.assert_allclose(scales, np.median(target/source))
    np.testing.assert_array_equal(shifts, 0.)
    assert report["scale_only_frames"] == [0]


def test_unfittable_frame_abstains_without_losing_the_scene():
    cameras, intrinsics, depth, frames, slots = fixture()
    baseline = make_export(cameras, intrinsics, depth, frames, slots, (480, 640), [0., -1., 0.])
    candidate = {key: value.copy() for key, value in baseline.items()}
    candidate["depth_grid"][0] = 0
    result, report = hybrid("frame_affine", baseline, candidate)
    validate_export(result)
    assert not result["depth_grid"][0].any()
    assert report["fit"]["abstained_frames"] == [0]
