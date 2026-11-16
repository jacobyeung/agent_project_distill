import numpy as np
import pytest

from geo_bakeoff.metrics import depth_statistics, pose_statistics, paired_bootstrap, edge_band


def test_depth_metrics_count_missing_predictions_as_errors():
    gt = np.ones((1, 16, 16))
    pred = gt.copy()
    pred[0, 0, 0] = 0
    row = depth_statistics(pred, gt, np.array([True]), np.zeros_like(gt, dtype=int))
    assert row["overall"]["absrel"] == pytest.approx(1 / 256)
    assert row["overall"]["delta1"] == pytest.approx(255 / 256)
    assert row["overall"]["prediction_coverage"] == pytest.approx(255 / 256)


def test_depth_edge_band_is_five_pixel_euclidean():
    d = np.ones((24, 40))
    d[:, 20:] = 2
    band = edge_band(d, radius=5)
    assert band[12, 14] and band[12, 25]
    assert not band[12, 13] and not band[12, 26]


def test_pose_metric_does_not_fit_scale():
    gt = np.repeat(np.eye(4)[None], 4, axis=0)
    gt[:, 0, 3] = np.arange(4)
    pred = gt.copy()
    pred[:, 0, 3] *= 1.2
    row = pose_statistics(pred, gt, np.ones(4, bool))
    assert row["rotation_deg"] == pytest.approx(0)
    assert row["centre_relative"] == pytest.approx(.2)
    assert row["translation_m"] == pytest.approx(.4)


def test_cluster_bootstrap_preserves_scenes_and_rejects_mismatches():
    rows = [{"id": str(i), "scene": "a" if i < 2 else "b", "score": .6} for i in range(3)]
    base = [{**r, "score": .4} for r in rows]
    out = paired_bootstrap(rows, base, draws=100)
    assert out["delta_points"] == pytest.approx(20)
    np.testing.assert_allclose(out["ci95"], [20, 20])
    assert out["scenes"] == 2
    with pytest.raises(ValueError):
        paired_bootstrap(rows, base[:-1])
