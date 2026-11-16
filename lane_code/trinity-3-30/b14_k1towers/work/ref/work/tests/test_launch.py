import json
import os
from pathlib import Path
import sys
import subprocess

import pytest

from geo_bakeoff.guard import guarded
from geo_bakeoff.io import footprint
from run_arm import check_review, cpu_capacity, kit_roots, check_resume_request


def test_only_two_eight_thread_reservations(tmp_path):
    with cpu_capacity(tmp_path), cpu_capacity(tmp_path):
        with pytest.raises(RuntimeError):
            with cpu_capacity(tmp_path):
                pass
    with cpu_capacity(tmp_path):
        pass


def test_review_binds_exact_kit_seal(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    review = inbox / "review.md"
    review.write_text("APPROVED\nkit_sha256: abc\n")
    check_review(review, tmp_path, "abc")
    with pytest.raises(PermissionError):
        check_review(review, tmp_path, "different")
    with pytest.raises(PermissionError):
        check_review(None, tmp_path, "abc")


def test_resume_cannot_change_its_epoch_or_membership():
    check_resume_request({"resume_identity": "fixed"}, "fixed")
    with pytest.raises(ValueError):
        check_resume_request({"resume_identity": "fixed"}, "different")


def test_lane_limit_does_not_charge_production_runs(tmp_path, monkeypatch):
    import geo_bakeoff.io as io
    kit, runs = tmp_path / "kit", tmp_path / "runs"
    kit.mkdir()
    runs.mkdir()
    (kit / "code").write_bytes(b"code")
    (runs / "results").write_bytes(b"x"*100)
    monkeypatch.setattr(io, "ROOT", kit)
    monkeypatch.setattr(io, "ASSETS", kit / "assets")
    monkeypatch.setattr(io, "OUTPUT_ROOT", runs)
    monkeypatch.setattr(io, "LANE_LIMIT", 10)
    monkeypatch.setenv("GEO_BAKEOFF_DATA_ROOT", str(kit / "data"))
    assert io.lane_footprint() == 4
    io.check_lane_budget(runs / "next", 1000)
    with pytest.raises(RuntimeError):
        io.check_lane_budget(kit / "next", 7)


def test_hard_links_count_once_in_asset_budget(tmp_path):
    first = tmp_path / "first"
    first.write_bytes(b"verified")
    os.link(first, tmp_path / "second")
    assert footprint(tmp_path) == len(b"verified")


def test_input_roots_cannot_bypass_the_sealed_bundle(tmp_path):
    assert kit_roots(tmp_path) == (tmp_path / "data", tmp_path / "assets")
    with pytest.raises(PermissionError):
        kit_roots(tmp_path, data=tmp_path.parent)
    with pytest.raises(PermissionError):
        kit_roots(tmp_path, assets=tmp_path.parent)


def test_kit_environment_ignores_unsealed_input_overrides(tmp_path):
    script = Path(__file__).resolve().parents[1] / "kit_env.sh"
    env = {"PATH": os.environ["PATH"], "GEO_BAKEOFF_ASSETS": "/scratch/unsealed_assets",
           "GEO_BAKEOFF_DATA_ROOT": "/scratch/unsealed_data"}
    command = f'source "{script}"\nprintf "%s\\n%s\\n" "$GEO_BAKEOFF_ASSETS" "$GEO_BAKEOFF_DATA_ROOT"\n'
    result = subprocess.run(["/bin/bash"], input=command, env=env, cwd=tmp_path,
                            text=True, capture_output=True, check=True)
    assert result.stdout.splitlines() == [str(script.parent.parent / "assets"), str(script.parent.parent / "data")]


def test_launch_ignores_an_external_interpreter(tmp_path):
    source = Path(__file__).resolve().parents[1]
    work = tmp_path / "work"
    binary = tmp_path / "runtime/base/bin"
    work.mkdir()
    binary.mkdir(parents=True)
    for name in ("launch.sh", "kit_env.sh"):
        (work / name).write_bytes((source / name).read_bytes())
    for path, marker in ((binary / "python3", "sealed"), (tmp_path / "foreign", "foreign")):
        path.write_text(f"#!/bin/sh\nprintf '{marker}\\n'\n")
        path.chmod(0o700)
    result = subprocess.run(["/bin/bash", str(work / "launch.sh"), "tower_g3t"],
                            env={"PATH": os.environ["PATH"], "GEO_BAKEOFF_PYTHON": str(tmp_path / "foreign")},
                            text=True, capture_output=True, check=True)
    assert result.stdout.strip() == "sealed"


def test_guard_pins_the_child_working_directory_and_safe_path(tmp_path, monkeypatch):
    trusted, foreign = tmp_path / "trusted", tmp_path / "foreign"
    trusted.mkdir()
    foreign.mkdir()
    (trusted / "target_module.py").write_text("print('sealed')\n")
    (foreign / "target_module.py").write_text("raise RuntimeError('foreign code')\n")
    monkeypatch.chdir(foreign)
    env = {key: value for key, value in os.environ.items() if key in ("PATH", "PYTHONHOME", "TMPDIR")}
    code = "import os,sys;assert sys.flags.safe_path;import target_module;print(os.getcwd())"
    guarded([sys.executable, "-c", code], tmp_path / "stage/progress.json", tmp_path / "events",
            "safe_path", tmp_path / "log", {**env, "PYTHONPATH": str(trusted)}, cwd=trusted)
    assert (tmp_path / "log").read_text().splitlines() == ["sealed", str(trusted)]


def test_guard_alerts_on_stall_without_killing_or_relaunching(tmp_path):
    output = tmp_path / "stage"
    output.mkdir()
    progress = output / "progress.json"
    code = ("import json,time;from pathlib import Path;"
            f"p=Path({str(progress)!r});p.write_text(json.dumps({{'state':'running'}}));"
            "time.sleep(.5);p.write_text(json.dumps({'state':'complete'}))")
    env = {key: value for key, value in os.environ.items() if key in ("PATH", "PYTHONHOME", "PYTHONPATH", "TMPDIR")}
    guarded([sys.executable, "-c", code], progress, tmp_path / "events", "cpu_test",
            tmp_path / "log", {**env, "CUDA_VISIBLE_DEVICES": ""}, seconds=.1)
    assert json.loads(progress.read_text())["state"] == "complete"
    assert list((tmp_path / "events").glob("*_BLOCKER_stall_cpu_test_*.md"))
