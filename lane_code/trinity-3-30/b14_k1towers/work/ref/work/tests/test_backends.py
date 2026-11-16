import numpy as np
import pytest

from geo_bakeoff.backends import clean_depth, pointmap_intrinsics, restore_intrinsics, read_rgb, pi3x_size, default_resolution
from geo_bakeoff.safety import validate_device


def test_joint_models_use_their_official_resolution_defaults():
    assert pi3x_size((480, 640)) == (434, 574)
    assert pi3x_size((640, 480)) == (574, 434)
    assert default_resolution("da3") == 504
    assert default_resolution("mapanything") == 518


def test_pointmap_focal_recovery():
    h, w, focal = 28, 42, 32.
    yy, xx = np.mgrid[:h, :w]
    points = np.stack([(xx + .5 - w / 2) / focal, (yy + .5 - h / 2) / focal, np.ones_like(xx)], -1)[None]
    k = pointmap_intrinsics(points)
    np.testing.assert_allclose(k[0], [[focal, 0, w / 2], [0, focal, h / 2], [0, 0, 1]])
    large = restore_intrinsics(k, (h, w), (2 * h, 2 * w))
    np.testing.assert_allclose(large[:, :2], k[:, :2] * 2)


def test_integer_pixel_intrinsics_are_converted_before_resize():
    k = np.array([[[100., 0, 258.5], [0, 100., 195.5], [0, 0, 1.]]])
    restored = restore_intrinsics(k, (392, 518), (480, 640), integer_centres=True)
    np.testing.assert_allclose(restored[0, :2, 2], [320., 240.])
    np.testing.assert_allclose(k[0, :2, 2], [258.5, 195.5])


def test_only_proven_shared_checkpoint_keys_are_expanded():
    import torch
    from geo_bakeoff.backends import load_tied_state_dict
    layer = torch.nn.Linear(2, 1)
    model = torch.nn.ModuleList([layer, layer])
    state = {"0.weight": torch.ones_like(layer.weight), "0.bias": torch.ones_like(layer.bias)}
    aliases = load_tied_state_dict(model, state)
    assert set(aliases) == {"1.weight", "1.bias"}
    np.testing.assert_array_equal(model[1].weight.detach().numpy(), [[1., 1.]])
    independent = torch.nn.ModuleList([torch.nn.Linear(2, 1), torch.nn.Linear(2, 1)])
    with pytest.raises(RuntimeError):
        load_tied_state_dict(independent, state)


def test_missing_depth_is_zero_not_a_finite_fabrication():
    np.testing.assert_array_equal(clean_depth(np.array([1., np.nan, np.inf, -1.])), [1., 0., 0., 0.])


def test_image_arrays_keep_original_pixels():
    array = np.zeros((12, 16, 3), np.uint8)
    array[5, 7] = [12, 34, 56]
    np.testing.assert_array_equal(np.array(read_rgb(array)), array)
    with pytest.raises(ValueError):
        read_rgb(array.astype(float))


def test_no_gpu_without_explicit_lane_approval(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    with pytest.raises(PermissionError):
        validate_device("cuda")
    with pytest.raises(PermissionError):
        validate_device("cuda", "/tmp/GO")
    validate_device("cpu")
    import os
    assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
