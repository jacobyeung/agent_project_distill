"""F1/F2 in production-style roots. Orchard runs from the job-private /tmp mount (/tmp/a_<job>_<token>);
a root with named ancestors is exposed to children as /proc/<pid>/fd/<n>, so the bind source is found
by its suffix rather than its logical spelling. Roots stay under /tmp (about 1 MB each)."""
import json, subprocess, sys, secrets
from pathlib import Path
import pytest

SIM = Path(__file__).with_name('sim_r_namespace.py')
KIT = Path(__file__).resolve().parents[1]/'kit'
WORDS = ('arkitscenes', 'scannet', 'av_dataengine_cot')


def _base():
    base = Path('/tmp')/('a_900000_'+secrets.token_hex(6)); base.mkdir(); return base


def _argv(root):
    code = SIM.read_text().split("ap=out[", 1)[0] + "sys.__stdout__.write(json.dumps(dict(out=out,target=str(J.AP/'19252904/e/bin/python'),ap=str(J.AP)))+'\\n')\n"
    r = subprocess.run([sys.executable, '-B', '-c', code, str(KIT), str(root)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_reviewer_sim_passes_in_orchard_tmp_root():
    r = subprocess.run([sys.executable, '-B', str(SIM), str(KIT), str(_base())], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    v = json.loads(r.stdout)
    assert v['exec_target_under_bound_ap'] and not v['argv_words_after_mapping'], v


@pytest.mark.parametrize('named', [False, True])
def test_F1_F2_hold_under_any_root(named):
    root = _base()
    if named:
        root = root/'orch_n30'/'b07_offread'/('r'+secrets.token_hex(4)); root.mkdir(parents=True)
    v = _argv(root); out = v['out']
    src = [i for i, a in enumerate(out) if a.endswith('/m/ap') and out[i-1] == '--bind']
    assert len(src) == 1, src
    dest = out[src[0]+1]
    assert dest == v['ap'] and v['target'].startswith(dest+'/'), (dest, v['target'])
    assert not sorted({w for a in out for w in WORDS if w in a.lower()})
    assert not any('orch_n30' in a or 'b07_offread' in a for a in out)
