import json

import numpy as np
import pytest

from geo_bakeoff.contract import make_export, write_export
from geo_bakeoff.inputs import bind_decoded_frames, compare_decoded, frame_hashes, verify_frame_hashes, manifest_identity
from geo_bakeoff.io import sha256
from geo_bakeoff.provenance import verify_export_receipt
from test_contract import fixture


def test_decoder_gate_accepts_close_rgb_and_rejects_an_ordinal_shift():
    references = [np.full((8, 8, 3), i*3, np.uint8) for i in range(64)]
    decoded = [value + np.uint8(1) for value in references]
    proof = compare_decoded(decoded, references)
    assert min(proof["psnr_db"]) > 45
    with pytest.raises(ValueError):
        compare_decoded(references[1:] + references[:1], references)


def test_decoded_frame_hashes_reject_a_changed_frame():
    frames = [np.zeros((3, 4, 3), np.uint8) for _ in range(64)]
    expected = frame_hashes(frames)
    assert verify_frame_hashes(frames, expected) == expected
    frames[17][0, 0, 0] = 1
    with pytest.raises(ValueError):
        verify_frame_hashes(frames, expected)


def test_frame_registry_binds_candidates_and_resume(tmp_path):
    entry = {"scene": "scene0011_00", "dense_indices": list(range(64)), "source_hw": [3, 4],
             "video_sha256": "video", "images": None, "decoded_registry": str(tmp_path / "frame_ids.json")}
    hashes = ["frame"]*64
    bind_decoded_frames(entry, hashes)
    bind_decoded_frames(entry, hashes)
    with pytest.raises(ValueError):
        bind_decoded_frames(entry, ["changed"] + hashes[1:])


def test_manifest_comparison_ignores_only_timestamps_and_its_own_digest():
    first = {"created_at": "one", "manifest_sha256": "x", "scenes": [{"video_sha256": "fixed"}]}
    second = {**first, "created_at": "two", "manifest_sha256": "y"}
    assert manifest_identity(first) == manifest_identity(second)
    second["scenes"] = [{"video_sha256": "changed"}]
    assert manifest_identity(first) != manifest_identity(second)


def test_parent_export_must_match_its_producer_receipt(tmp_path):
    c, k, d, f, s = fixture()
    path = tmp_path / "scannet__scene0011_00.npz"
    write_export(path, make_export(c, k, d, f, s, (480, 640), [0., -1., 0.]))
    (tmp_path / "config.json").write_text('{"model":"synthetic"}')
    receipt = {"scene": "scene0011_00", "export_sha256": sha256(path)}
    (tmp_path / "summary.json").write_text(json.dumps({
        "status": "complete", "scenes": 1, "receipts": [receipt],
        "configuration_sha256": sha256(tmp_path / "config.json")}))
    assert verify_export_receipt(tmp_path, "scene0011_00") == receipt
    with path.open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError):
        verify_export_receipt(tmp_path, "scene0011_00")
