"""Mutant run: every guard threshold flipped (and key scoring rules altered) must fail a test.
Run: python -I -B tests/mutants.py  -> writes a JSON summary to stdout; exit 1 if a mutant survives."""
import json, os, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = (HERE.parent / "guard_read.py").read_text()
MUTANTS = [
    ("interval_uses_lower_bound", 'return comparison["interval"][1] < 0', 'return comparison["interval"][0] < 0'),
    ("interval_le_zero", 'return comparison["interval"][1] < 0', 'return comparison["interval"][1] <= 0'),
    ("interval_lt_minus_one", 'return comparison["interval"][1] < 0', 'return comparison["interval"][1] < -1'),
    ("camera_calls_allow_one_miss", "pass_=cam_calls == len(camera_keys)", "pass_=cam_calls >= len(camera_keys) - 1"),
    ("metre_rate_strict_gt", "pass_=m_calls >= METRE_CALL_RATE_MIN * len(metre)", "pass_=m_calls > METRE_CALL_RATE_MIN * len(metre)"),
    ("metre_rate_090", "METRE_CALL_RATE_MIN = 0.95", "METRE_CALL_RATE_MIN = 0.90"),
    ("metre_rate_096", "METRE_CALL_RATE_MIN = 0.95", "METRE_CALL_RATE_MIN = 0.96"),
    ("camera_interval_guard_always_pass", 'guards.append(dict(name="interval_" + t, pass_=not wholly_below_zero(c),', 'guards.append(dict(name="interval_" + t, pass_=True,'),
    ("metre_interval_guard_always_pass", 'guards.append(dict(name="interval_distance_metre", pass_=not wholly_below_zero(c),', 'guards.append(dict(name="interval_distance_metre", pass_=True,'),
    ("verdict_any_instead_of_all", 'verdict="PASS" if all(g["pass"] for g in guards)', 'verdict="PASS" if any(g["pass"] for g in guards)'),
    ("nonanswer_never", '    decoded = row.get("decode") or {}\n    if row.get("geometry_refusal")', '    return False\n    decoded = row.get("decode") or {}\n    if row.get("geometry_refusal")'),
    ("geometry_refusal_scores", 'if row.get("geometry_refusal") or row.get("refusal"):', 'if row.get("refusal"):'),
    ("think_close_ignored", 'if "text" in decoded and not re.search', 'if False and "text" in decoded and not re.search'),
    ("label_swapped", 'return "released_answer" if row.get("stratum") == "primary" else "answer"', 'return "answer" if row.get("stratum") == "primary" else "released_answer"'),
    ("seed_changed", "SEED = 20261115", "SEED = 20261116"),
    ("draws_5000_allowed", "require(draws >= 10000,", "require(draws >= 5000,"),
    ("quantile_90", "interval=[quantile(values, 0.025), quantile(values, 0.975)]", "interval=[quantile(values, 0.05), quantile(values, 0.95)]"),
    ("unweighted_rooms", "values.append(100.0 * sum(c[1] for c in chosen) / sum(c[0] for c in chosen))", "values.append(100.0 * sum(c[1] / c[0] for c in chosen) / len(chosen))"),
    ("difference_reversed", "difference=100.0 * sum(p[1] - p[2] for p in pairs) / n", "difference=100.0 * sum(p[2] - p[1] for p in pairs) / n"),
    ("missing_candidate_allowed", 'require(not missing_cand, "candidate arm lacks', 'require(True or not missing_cand, "candidate arm lacks'),
    ("list_sha_unchecked", 'require(sha256_file(list_path) == list_sha,', 'require(True or sha256_file(list_path) == list_sha,'),
    ("parser_sha_unchecked", 'require(sha256_file(path) == expected_sha,', 'require(True or sha256_file(path) == expected_sha,'),
    ("unit_check_skipped", 'require(parsed["unit"] == row["unit"] and', 'require(True or parsed["unit"] == row["unit"] and'),
    ("baseline_identity_unchecked", 'require(base_artifact == baseline_artifact,', 'require(True or base_artifact == baseline_artifact,'),
    ("room_pairing_unchecked", 'require(a["room"] == b["room"],', 'require(True or a["room"] == b["room"],'),
]
results, survivors = [], []
with tempfile.TemporaryDirectory() as tmp:
    for name, old, new in MUTANTS:
        count = SRC.count(old)
        if count != 1:
            results.append(dict(name=name, error="pattern occurs %d times" % count)); survivors.append(name); continue
        path = Path(tmp) / ("m_" + name + ".py")
        path.write_text(SRC.replace(old, new))
        env = dict(os.environ, GUARD_READ_PATH=str(path))
        run = subprocess.run([sys.executable, "-B", str(HERE / "test_guard_read.py")], env=env,
                             capture_output=True, text=True, timeout=900)
        killed = run.returncode != 0
        failing = sorted({l.split()[1] for l in run.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))})
        results.append(dict(name=name, killed=killed, failing_tests=failing))
        if not killed:
            survivors.append(name)
print(json.dumps(dict(mutants=len(MUTANTS), killed=len(MUTANTS) - len(survivors), survivors=survivors, results=results), indent=1))
sys.exit(1 if survivors else 0)
