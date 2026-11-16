import pytest

from geo_bakeoff.contract import make_export, write_export
from geo_bakeoff.io import dump_json, sha256
from geo_bakeoff.resume import prepare_stage, resume_scene
from test_contract import fixture


def test_resume_requires_explicit_matching_configuration(tmp_path):
    root = tmp_path / "stage"
    config = {"model": "synthetic", "input_sha256": "fixed", "resume": False}
    prepare_stage(root, config)
    with pytest.raises(FileExistsError):
        prepare_stage(root, config)
    prepare_stage(root, {**config, "resume": True}, resume=True)
    with pytest.raises(ValueError):
        prepare_stage(root, {**config, "input_sha256": "changed"}, resume=True)


def test_resume_reuses_only_verified_scenes_and_preserves_corrupt_outputs(tmp_path):
    root = prepare_stage(tmp_path / "stage", {"model": "synthetic"})
    c, k, d, f, s = fixture()
    path = root / "scannet__scene0011_00.npz"
    write_export(path, make_export(c, k, d, f, s, (480, 640), [0., -1., 0.]))
    row = {"scene": "scene0011_00", "export_sha256": sha256(path),
           "frame_indices": f.tolist(), "decoded_frame_sha256": ["rgb"]*64}
    dump_json(root / "receipts/scene0011_00.json", row)
    entry = {"dense_indices": f.tolist(), "decoded_sha256": ["rgb"]*64}
    assert resume_scene(root, "scene0011_00", entry=entry) == row
    assert path.exists()
    with path.open("ab") as stream:
        stream.write(b"corrupt")
    assert resume_scene(root, "scene0011_00", entry=entry) is None
    assert not path.exists()
    preserved = list((root / "preserved").glob("*/scannet__scene0011_00.npz"))
    assert len(preserved) == 1 and preserved[0].read_bytes().endswith(b"corrupt")
