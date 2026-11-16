from argparse import Namespace
from pathlib import Path
import io
import tarfile
import pytest
from offnative.cli import prepare,submission,checked
from offnative.io import dump,sha,load,extract,tar_bytes
from offnative.paths import ROOT,V1,module


def args(dest, manifest):
    return Namespace(benchmark='revsi999t32',export='step544',reader='e2e:'+sha(manifest),mode='fixture',
        freeze_file=None,e2e_manifest=str(manifest),eat1_report=None,init_selection=None,ledger=str(dest.parent/'ledger.jsonl'),
        export_layout=None,override_reason=None,frames=32,frame_layout='duplicate',destination=str(dest),token='a'*24)

def test_prepare_opaque_config_and_refuse_submission(tmp_path):
    p=tmp_path/'manifest.json';dump(p,{'fixture':True})
    a=args(tmp_path/'prepare',p)
    result=prepare(a)
    assert result['verdict']=='BLOCKED'
    config=(Path(a.destination)/'CONFIG.json').read_text()
    assert 'revsi' not in config.lower() and 'harness' not in config.lower() and 'e2e' not in config.lower()
    assert load(Path(a.destination)/'BINDING.json')['read_config']['frames']['count']==32
    with pytest.raises(ValueError):submission(a)
    c=load(Path(a.destination)/'CONFIG.json');c['x0']='0'*64;dump(Path(a.destination)/'CONFIG.json',c)
    with pytest.raises(ValueError):checked(a.destination)

def test_archive_traversal_rejected_before_write(tmp_path):
    p=tmp_path/'bad.tar'
    with tarfile.open(p,'w') as f:
        good=tarfile.TarInfo('safe');good.size=1;f.addfile(good,io.BytesIO(b'a'))
        bad=tarfile.TarInfo('../escape');bad.size=1;f.addfile(bad,io.BytesIO(b'b'))
    with pytest.raises(ValueError):extract(p,tmp_path/'dest')
    assert not (tmp_path/'dest/safe').exists()

def test_inherited_item_cutoff_and_return_reserve():
    B=module('_native_v1_budget',V1/'budget.py').Budget
    b=B('1970-01-01T01:00:00Z',clock=lambda:2900)
    assert b.return_seconds==600
    assert not b.allows('object_abs_distance')
    assert b.item_cutoff()==2875
