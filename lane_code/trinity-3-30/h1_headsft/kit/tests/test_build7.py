"""Run reviewed-reader probes in a fresh interpreter, isolated from the frozen test reader."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

K=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def reviewed(tmp_path_factory):
    out=tmp_path_factory.mktemp('reviewed')
    result=subprocess.run([sys.executable,'-B',str(K/'tests/build7_probe.py'),str(out)],
                          env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),text=True,capture_output=True)
    (out/'probe.log').write_text(result.stdout+'\n'+result.stderr)
    assert result.returncode==0,result.stdout[-2000:]+result.stderr[-5000:]
    return json.loads((out/'RESULT.json').read_text())

def test_reviewed_signature(reviewed):
    assert 'settings' in reviewed['signature']

def test_real_item_mapping(reviewed):
    assert reviewed['mapping']['count']==636
    assert reviewed['mapping']['dense_counts']=={'32':69,'64':567}
    assert reviewed['mapping_refusals'] and reviewed['revsi_staged_binding']

def test_keyword_perception_and_target_modes(reviewed):
    assert reviewed['keywords_modes_finite']
    assert reviewed['stageone_artifact_cache']

def test_reviewed_cpu_first_batch(reviewed):
    assert reviewed['cpu_eight_reads']==dict(count=8,passed=True,loads=1)

def test_reviewed_resume(reviewed):
    assert reviewed['reviewed_launch_resume']['completed']==reviewed['reviewed_launch_resume']['expected']

def test_tower_journals(reviewed):
    assert reviewed['tower_conversion']['count']==2
    assert len(reviewed['tower_conversion']['refusals'])==7

def test_registered_read_counts(reviewed):
    assert reviewed['read_counts']['devs1']==dict(own_baseline=636,own_perturbed=900,tower=636,tower_reused=636,reads=1536)
    assert reviewed['read_counts']['revsi']==dict(own_baseline=999,own_perturbed=566,tower=999,tower_reused=999,reads=1565)


def test_native_tree_bootstrap(tmp_path):
    root=Path('/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449')
    settings=tmp_path/'bootstrap.json'
    settings.write_text(json.dumps({'tree':str(root)}))
    code='''
from pathlib import Path
import h1eval.items
from h1eval.h10.launch import reader_factory
reader_factory('/scratch/jjyeung/orch_n30/b04_e2ehook')
from h1eval.h10.parity_adapter import prepare_runtime, settings_for
import os
s=settings_for(os.environ['H10_SETTINGS'], 'devs1_routed')
assert os.environ['H10_OVERLAY'] in s['env_roots']
prepare_runtime({'tree':TREE})
from student_pilot import carrier_c1_routing, camera_targets
assert Path(carrier_c1_routing.__file__).resolve().is_relative_to(TREE)
assert Path(camera_targets.__file__).resolve().is_relative_to(TREE)
assert len(h1eval.items.load_manifest('items/devs1_routed.json')['items'])==636
'''.replace('TREE',repr(str(root)))
    result=subprocess.run([sys.executable,'-B','-c',code],text=True,capture_output=True,
                          env=dict(os.environ,H10_SETTINGS=str(settings),H10_OVERLAY=str(tmp_path)),cwd=K)
    assert result.returncode==0,result.stderr


def test_host_wrapper_busy_card(tmp_path):
    binary=tmp_path/'nvidia-smi'
    binary.write_text('#!/bin/bash\necho 1025\n');binary.chmod(0o755)
    env=dict(os.environ,PATH=str(tmp_path)+os.pathsep+os.environ['PATH'])
    result=subprocess.run(['bash',str(K/'h1eval/h10/host_run.sh'),'0','devs1_routed','own','0/3',str(tmp_path/'run')],
                          env=env,text=True,capture_output=True)
    assert result.returncode==3 and 'busy' in result.stderr
    assert not (tmp_path/'run').exists()
