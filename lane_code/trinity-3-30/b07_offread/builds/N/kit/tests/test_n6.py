"""Production boundary regressions, independent of reviewer tests."""
import json,os,subprocess,sys
from pathlib import Path
import pytest
from offnative.paths import ROOT

def test_shards_charge_full_work_and_keep_scenes_together():
    from offnative.shards import plan,LIMIT,RESERVE
    from offnative.cohort import cohort,canary
    from offkit.report import key,ReadMode
    items=cohort('vsibench5130');p=plan(items);seen={};ids=[]
    by={key(r):r for r in items}
    for shard in p['shards']:
        assert shard['estimated_seconds']==1.25*sum(shard['cost_terms'].values())+RESERVE
        assert shard['estimated_seconds']<=LIMIT
        assert shard['cost_terms']['proof_second_load_s']>0
        assert shard['cost_terms']['scene_sam_s']>0
        rows=[by[k] for k in shard['ids']]
        assert len(canary(rows,ReadMode('vsibench5130','harness')))==10
        for row in rows:
            scene=(row['dataset'],row['scene_name'])
            assert seen.setdefault(scene,shard['index'])==shard['index']
        ids+=shard['ids']
    assert len(seen)==288 and len(ids)==len(set(ids))==5130
    assert p==plan(list(items))
    with pytest.raises(ValueError):plan(items,count=1)

def test_child_argv_media_resolution_and_logs(tmp_path):
    from offnative.opacity import scan
    (tmp_path/'xnames.py').write_bytes((ROOT/'offnative/opacity.py').read_bytes())
    code=r"""import os,sys,subprocess
from pathlib import Path
import xnames as X
root=Path.cwd();(root/'v').mkdir();target=root/'v'/('a'*64+'.mp4');target.write_bytes(b'fixture')
X.media_alias('/project/community/jjyeung/3e0e8a36/arkitscenes/1.mp4',target)
X.install(root)
import av
try:av.open('/project/community/jjyeung/3e0e8a36/arkitscenes/1.mp4')
except av.error.InvalidDataError:pass
else:raise AssertionError('fixture bytes unexpectedly decoded')
for name in ('WATCHDOG.json.log','chain.log'):
 before=len(os.listdir('/proc/self/fd'))
 with open(root/name,'wb') as log:
  fd=log.fileno()
  for i in range(30):assert log.fileno()==fd
  subprocess.run([sys.executable,'-B','-c',"from pathlib import Path;assert Path('/project/community/jjyeung/3e0e8a36/arkitscenes/1.mp4').read_bytes()==b'fixture';print('child retained');print('vsi')"],check=True,stdout=log,stderr=log)
 assert len(os.listdir('/proc/self/fd'))==before
 assert b'child retained' in (root/name).read_bytes()
 assert b'vsi' not in (root/name).read_bytes()
for args in (['/bin/echo','arkitscenes'],['/bin/sh','-c','echo scannet'],['/bin/echo','767369']):
 try:subprocess.run(args,check=True)
 except ValueError:pass
 else:raise AssertionError('argv leak admitted')
print('passed')
"""
    result=subprocess.run([sys.executable,'-B','-c',code],cwd=tmp_path,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=='passed'
    for name in ('WATCHDOG.json.log','chain.log'):scan((tmp_path/name).read_bytes())

def test_shard_staging_uses_only_its_media(tmp_path,monkeypatch):
    from offnative import portable,stage_plan
    from offnative.shards import plan
    from offnative.cohort import cohort,media_manifest
    from offnative.io import dump
    items=cohort('vsibench5130');shard=plan(items)['shards'][0]
    config={'shard':shard,'token':'a'*24,'pool':'/p'}
    binding={'benchmark':'vsibench5130','reader':{'kind':'harness'},'mode':'fixture',
             'binding_sha256':'a'*64,'export':{'kind':'fixture','sha256':'b'*64},
             'read_config':{'frames':{},'g3t':{}},'arms':['primary']}
    expected={dataset+'/'+scene+'.mp4' for dataset,scene in shard['scenes']}
    captured={}
    def stage(binding,inputs,*args):
        assert {r['relative_path'] for r in inputs['media']}==expected
        captured['stage']=inputs
        return {},{}
    def packet(files,*args):
        captured['worker']=json.loads(files['p.json'])
        return {'sha256':'c'*64}
    monkeypatch.setattr(stage_plan,'prepare',stage)
    monkeypatch.setattr(portable,'sources',lambda:({},{}))
    monkeypatch.setattr(portable,'pack',lambda files:(files,[]))
    monkeypatch.setattr(portable,'packet',packet)
    dump(tmp_path/'CONFIG.json',config)
    portable.build(tmp_path,config,binding,items,{'media':media_manifest('vsibench5130',items)})
    assert {r['relative_path'] for r in captured['worker']['inputs']['media']}==expected
    assert len(captured['worker']['items'])==5130
