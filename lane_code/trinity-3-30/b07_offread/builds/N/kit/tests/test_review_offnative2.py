"""Reviewer refute tests (review_offnative2). R cases: run from builds/R with ROFF2_SIM pointing at
sim_r_namespace.py; N case: copy into builds/N/kit/tests. Each asserts the brief's contract."""
import json, os, subprocess, sys, secrets
from pathlib import Path
import pytest

SIM = os.environ.get('ROFF2_SIM', str(Path(__file__).with_name('sim_r_namespace.py')))
# Production roots live under /tmp on Orchard; any root outside /dev/shm takes xnames' production branch.
PROD_ROOT_PARENT = os.environ.get('ROFF2_ROOT', '/scratch/jjyeung/orch_n30/review_offnative2/work')


def _sim():
    kit = Path.cwd()/'kit'
    if not (kit/'vsi/launcher/orchard_job.py').is_file():
        pytest.skip('run from builds/R')
    root = Path(PROD_ROOT_PARENT)/('r'+secrets.token_hex(4)); root.mkdir(parents=True)
    r = subprocess.run([sys.executable, '-B', SIM, str(kit), str(root)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_F1_direct_vllm_interpreter_reachable_in_namespace():
    """vllm_isolated.sh (/bin/sh, no xnames) execs the logical AP path; the namespace must mount it there."""
    v = _sim()
    assert v['exec_target_under_bound_ap'], (v['vllm_isolated_sh_exec_target'], v['ap_bind_destination_in_namespace'])


def test_F2_namespace_argv_has_no_dataset_word():
    """AGENTS.md: no argument may carry a benchmark or dataset word; bwrap's argv is visible to every user."""
    v = _sim()
    assert not v['argv_words_after_mapping'], (v['media_binds_with_dataset_word'], v['media_bind_example'])


def test_F3_shard_estimate_charges_each_shards_own_scenes():
    """Each shard stages, towers and proposes every scene its items touch; the 6 h fit must charge them."""
    try:
        from offnative.shards import plan, cost, LIMIT, RESERVE
        from offnative.cohort import cohort
        from offkit.report import key
    except ImportError:
        pytest.skip('run from builds/N/kit/tests')
    items = cohort('vsibench5130'); p = plan(items); by = {key(r): r for r in items}
    for s in p['shards']:
        rows = [by[k] for k in s['ids']]
        scenes = {(r['dataset'], r['scene_name']) for r in rows}
        honest = 1.25*(sum(cost(r) for r in rows)+3.8*len(scenes))
        assert s['estimated_seconds'] >= honest, (s['index'], len(scenes), s['estimated_seconds'], honest)
