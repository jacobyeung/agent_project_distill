import base64,io,json,re,subprocess,sys,tarfile
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kit'))
import xnames

@pytest.mark.parametrize('benchmark',['vsibench5130','revsi999t32'])
def test_actual_batch_paths_environment_and_submit(tmp_path,benchmark):
    code="""from pathlib import Path
import sys,json,re
sys.path.insert(0,str(Path(sys.argv[1])/'kit'))
import rebind
from argparse import Namespace
p=Path(sys.argv[2]);rebind.prepare(Namespace(benchmark=sys.argv[3],export='step544',mode='production',init_selection=None,ledger=p.parent/'ledger.jsonl',token='a0123456789',destination=p))
L=rebind.launcher(sys.argv[3]);print(json.dumps(L.submit_argv(None,'a0123456789')))
"""
    d=tmp_path/'p'
    r=subprocess.run([sys.executable,'-B','-c',code,str(ROOT),str(d),benchmark],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    xnames.scan(r.stdout)
    script=(d/'BATCH.sh').read_text();xnames.scan(script)
    raw=bytes.fromhex(re.search(r"^raw=bytes.fromhex\('([0-9a-f ]+)'",script,re.M)[1])
    assert xnames.scan_members(raw)>=90
    with pytest.raises(ValueError):xnames.scan('LEGS1_TREE=/tmp/official999')
    with pytest.raises(ValueError):xnames.scan('A0_ROOTS=/tmp/revsi')
