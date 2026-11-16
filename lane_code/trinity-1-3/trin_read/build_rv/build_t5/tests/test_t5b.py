import argparse
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from types import SimpleNamespace as NS

import pytest
import trinity_read as T
import milestone as M

E193 = Path('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193')


@pytest.mark.parametrize('run', ['469ddece', '359fcc3c'])
@pytest.mark.parametrize('step', [1, 100, 200, 400, 800, 1000, 123456])
def test_export_allowlist(tmp_path, run, step):
    p = T.FSW/'ap/8865619b/runs'/run/('m'+str(step))/'artifact.json'
    assert T.logical_artifact(tmp_path, str(p), step) == str(p)
    assert T.logical_artifact(tmp_path, str(T.physical(tmp_path, p)), step) == str(p)


@pytest.mark.parametrize('path,step', [('8865619b/runs/deadbeef/m100', 100),
    ('11111111/runs/359fcc3c/m100', 100), ('8865619b/runs/359fcc3c/m0', 0),
    ('8865619b/runs/359fcc3c/m100', 200), ('8865619b/runs/359fcc3c/../359fcc3c/m100', 100)])
def test_export_refusals(tmp_path, path, step):
    with pytest.raises(ValueError): T.logical_artifact(tmp_path, str(T.FSW/'ap'/path/'artifact.json'), step)


def archive_fixture(tmp_path, extra=None):
    source = tmp_path/'359fcc3c_m100.tar'
    with tarfile.open(str(source), 'w') as tf:
        for name in ('artifact.json', 'heads.pt', 'full_weights/full_weights.json'):
            raw = b'{}'; info = tarfile.TarInfo('m100/'+name); info.size = len(raw)
            tf.addfile(info, io.BytesIO(raw))
        if extra is not None:
            info = tarfile.TarInfo(extra[0]); info.type = extra[1]
            if info.islnk() or info.issym(): info.linkname = 'm100/artifact.json'
            tf.addfile(info)
    done = tmp_path/'DONE.json'
    T.dump(done, dict(object='gs://bucket/359fcc3c_m100.tar', bytes=source.stat().st_size, sha256=T.sha(source)))
    return NS(root=str(tmp_path/'root'), tar=str(source), done=str(done), run='359fcc3c', step=100, full=False, bwrap='/usr/bin/bwrap')


def fake_stage(monkeypatch, fail=False):
    monkeypatch.setattr(T, 'kit_stage', lambda:NS(room=lambda *a:None))
    def check(root, artifact, digest, step, full, receipt, bwrap):
        if fail: raise RuntimeError('checker failed')
        assert T.load(receipt/'RECEIPT.json')['status'] == 'extracted'
        return dict(status='VERIFIED' if full else 'HEADER_ONLY_NOT_VERIFIED', step=step)
    monkeypatch.setattr(M, 'run_export_checker', check)


@pytest.mark.parametrize('full', [False, True])
def test_stage_receipt_and_no_overwrite(tmp_path, monkeypatch, full):
    a = archive_fixture(tmp_path); a.full = full; fake_stage(monkeypatch)
    r = M.stage_export(a)
    assert r['status'] == 'complete' and r['checker']['status'] == ('VERIFIED' if full else 'HEADER_ONLY_NOT_VERIFIED')
    dest = Path(a.root)/'fsw/ap/8865619b/runs/359fcc3c/m100'
    assert (dest/'heads.pt').read_bytes() == b'{}'
    with pytest.raises(ValueError, match='exists'): M.stage_export(a)


@pytest.mark.parametrize('field,value', [('bytes', 1), ('sha256', '0'*64), ('object', ''), ('bytes', True)])
def test_stage_done_mismatch(tmp_path, monkeypatch, field, value):
    a = archive_fixture(tmp_path); fake_stage(monkeypatch)
    d = T.load(a.done); d[field] = value; T.dump(a.done, d)
    with pytest.raises(ValueError): M.stage_export(a)
    assert not (Path(a.root)/'fsw').exists()


@pytest.mark.parametrize('extra', [('/m100/x', tarfile.REGTYPE), ('m100/../x', tarfile.REGTYPE),
    ('m200/x', tarfile.REGTYPE), ('m100/full_weights/link', tarfile.SYMTYPE),
    ('m100/full_weights/hard', tarfile.LNKTYPE), ('m100/full_weights/dev', tarfile.CHRTYPE),
    ('m100/full_weights/fifo', tarfile.FIFOTYPE), ('m100/artifact.json', tarfile.REGTYPE),
    ('m100/extra', tarfile.REGTYPE), ('m100/heads.pt/child', tarfile.REGTYPE)])
def test_stage_unsafe_or_different_layout(tmp_path, monkeypatch, extra):
    a = archive_fixture(tmp_path, extra); fake_stage(monkeypatch)
    with pytest.raises(ValueError): M.stage_export(a)
    assert not (Path(a.root)/'fsw').exists()


def test_stage_part_and_symlink(tmp_path):
    a = archive_fixture(tmp_path)
    part = tmp_path/'weights.part.tar'; part.write_bytes(Path(a.tar).read_bytes())
    a.tar = str(part)
    with pytest.raises(ValueError, match='part'): M.stage_export(a)
    link = tmp_path/'linked.tar'; link.symlink_to(part)
    a.tar = str(link)
    with pytest.raises(ValueError): M.stage_export(a)


def test_checker_failure_retains_export_and_receipt(tmp_path, monkeypatch):
    a = archive_fixture(tmp_path); fake_stage(monkeypatch, fail=True)
    with pytest.raises(RuntimeError): M.stage_export(a)
    receipt = T.load(Path(a.root)/'exports/359fcc3c_m100/RECEIPT.json')
    assert receipt['status'] == 'failed' and receipt['artifact_sha256']
    assert T.physical(Path(a.root), receipt['artifact']).exists()
    with pytest.raises(ValueError, match='exists'): M.stage_export(a)


def test_e193_inventory_and_primary_rule():
    inv = M.inventory()
    assert {f:len(r['items']) for f,r in inv.items()} == dict(main=1525, away=150, forward=150, camera=450)
    for family in T.FAMILIES:
        report = T.load(E193/'merged'/family/'report/B2048.json')
        scores = M.primary_scores(report, family)
        assert scores['total_items'] == len(inv[family]['items'])
        if family == 'main':
            assert scores['overall']['score_pct'] == report['summary']['primary']['released_answer']['overall']['score_pct']
            assert scores['overall']['items'] == 1375
            assert scores['per_task']['route_planning']['scoring_basis'] == 'answer'
            assert scores['per_task']['object_abs_distance']['scoring_basis'] == 'released_answer'
        else:
            own = next(iter(report['own_gt_by_stratum'].values()))['overall']
            assert scores['overall']['score_pct'] == own['score_pct']
        M.validate_membership(family, list(inv[family]['items']))
        with pytest.raises(ValueError): M.validate_membership(family, list(inv[family]['items'])[1:])


def args_for(tmp_path):
    return NS(command='read', root=str(tmp_path), out=str(tmp_path/'packets'), gpu='3', token='d123456789',
              families=None, all_families=True, ids=None, first=None, model_slot=None,
              artifact=str(T.FSW/'ap/8865619b/runs/359fcc3c/m100/artifact.json'),
              sha256='a'*64, step=100, yield_glob=str(tmp_path/'*.yield'))


@pytest.mark.parametrize('failure', [None, 'away', 'yield'])
def test_multifamily_order_and_stop(tmp_path, monkeypatch, failure):
    a = args_for(tmp_path); calls = []
    def launch(child):
        calls.append((child.family, child.gpu, child.token, child.out))
        assert child.ids is None and child.first is None
        if child.family == failure: raise RuntimeError('family failure')
        if failure == 'yield': (tmp_path/'stop.yield').write_text('yield')
    monkeypatch.setattr(T, 'launch', launch)
    monkeypatch.setattr(M, 'family_summary', lambda *a:dict(status='complete', total_items=3, per_task={}))
    if failure:
        with pytest.raises(RuntimeError): M.read_families(a)
    else: M.read_families(a)
    assert [x[0] for x in calls] == (list(T.FAMILIES) if failure is None else ['main','away'] if failure == 'away' else ['main'])
    assert all(x[1] == '3' and x[3] == str(tmp_path/'packets'/x[0]) for x in calls)
    assert len({x[2] for x in calls}) == len(calls)
    summary = T.load(tmp_path/'packets/MILESTONE_SUMMARY.json')
    assert summary['status'] == ('complete' if failure is None else 'yielded' if failure == 'yield' else 'failed')
    assert (tmp_path/'packets/MILESTONE_SUMMARY.md').exists()
    with pytest.raises(ValueError, match='exists'): M.read_families(a)


def test_yield_before_first_family(tmp_path, monkeypatch):
    a = args_for(tmp_path); (tmp_path/'stop.yield').touch()
    monkeypatch.setattr(T, 'launch', lambda a:pytest.fail('Must not launch'))
    with pytest.raises(RuntimeError, match='Yield'): M.read_families(a)
    assert T.load(tmp_path/'packets/YIELD.json')['next_family'] == 'main'


@pytest.mark.parametrize('families', ['', 'main,main', 'main,bad', 'main, away'])
def test_bad_families(families):
    with pytest.raises(ValueError): M.parse_families(families)


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows))


def cost_fixture(tmp_path):
    proof = tmp_path/'proof_r1'; dest = proof/'b0/d0/results'
    for arm, folder in M.C.ARMS.items():
        rows = [dict(example_id=k, key='devrows:'+k, status='complete', seconds=10, token_ids=[1,2,3]) for k in ('a','b')]
        jsonl(dest/folder/'items_b0.jsonl', rows)
        name = 'g0.jsonl' if arm == 'ON16k' else 'budget_'+arm[1:]+'.g0.jsonl'
        jsonl(dest/'0'/name, rows)
        if arm != 'ON16k':
            jsonl((dest/'0'/name).with_suffix('.meta.jsonl'), [dict(source_key='devrows:'+k,
                answer_cap_policy='reuse_full_on_answer' if k == 'a' else 'continuation_64') for k in ('a','b')])
    T.dump(proof/'EXIT.json', dict(returncode=0, wall_seconds=60, sampler_errors=[]))
    return proof


def test_cost_one_card_projection_and_reuse(tmp_path):
    proof = cost_fixture(tmp_path); value = M.cost(proof)
    assert value['arms']['ON16k']['seconds_per_item'] == 10
    assert value['arms']['B2048']['seconds_per_item'] == 5
    assert value['arms']['B2048']['reused_items'] == 1
    assert sum(a['allocated_wall_seconds_per_item'] for a in value['arms'].values()) == 30
    assert value['milestone_items'] == 2275 and value['projected_wall_minutes'] == 1137.5
    assert T.load(proof/'COST.json') == value
    result = subprocess.run([sys.executable, '-B', str(T.BUILD/'trinity_read.py'), 'cost', '--proof', str(proof)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    assert result.returncode == 0 and json.loads(result.stdout) == value


def test_cost_refuses_failed_and_missing_latency(tmp_path):
    proof = cost_fixture(tmp_path)
    T.dump(proof/'EXIT.json', dict(returncode=75, wall_seconds=60))
    with pytest.raises(ValueError): M.cost(proof)
    T.dump(proof/'EXIT.json', dict(returncode=0, wall_seconds=60))
    jsonl(proof/'b0/d0/results/0/g0.jsonl', [])
    with pytest.raises(ValueError, match='latency'): M.cost(proof)


def test_cli_full_read_selection(monkeypatch, tmp_path):
    seen = []; monkeypatch.setattr(T, 'launch', seen.append)
    base = ['trinity_read.py','read','--artifact','path','--sha256','a'*64,'--step','100','--gpu','0','--token','d123456789','--out',str(tmp_path)]
    for flags in ([], ['--all-families'], ['--families','main,away,forward,camera'], ['--family','main']):
        monkeypatch.setattr(sys, 'argv', base+flags); T.main()
        assert seen[-1].ids is None and seen[-1].first is None
    monkeypatch.setattr(sys, 'argv', base+['--all-families','--first','20'])
    with pytest.raises(SystemExit): T.main()


def test_unchanged_checker_header_and_full_modes(tmp_path):
    """Exercise the real checker on miniature BF16 headers, without a namespace or model."""
    import struct
    checker = Path('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27c/r2/sj/orch_cd/legs1_reads/out/export_check.py')
    assert T.sha(checker) == M.CHECKER_PINS['export_check.py']
    milestone = tmp_path/'m100'; weights = milestone/'full_weights'; weights.mkdir(parents=True)
    base = tmp_path/'base'; base.mkdir()
    header = json.dumps({'x':dict(dtype='BF16',shape=[1],data_offsets=[0,2])}).encode()
    raw = struct.pack('<Q',len(header))+header+b'\0\0'
    (base/'model.safetensors').write_bytes(raw)
    shard = weights/'model.safetensors'; shard.write_bytes(raw)
    index = weights/'model.safetensors.index.json'; T.dump(index,dict(weight_map={'x':shard.name}))
    manifest = weights/'full_weights.json'
    T.dump(manifest,dict(schema='full-ft-export-v1',dtype='bfloat16',tensor_count=1,
        index=dict(name=index.name,sha256=T.sha(index)),
        files=[dict(name=shard.name,bytes=len(raw),sha256=T.sha(shard),tensors=1)]))
    artifact = milestone/'artifact.json'
    def artifact_update():
        T.dump(artifact,dict(schema='carrier-c1-artifact-v1',step=100,
                            full_weights=dict(path=str(manifest),sha256=T.sha(manifest))))
    artifact_update()
    def run(name, header_only):
        command = [sys.executable,'-B',str(checker),'--export',str(artifact),'--sha256',T.sha(artifact),
                   '--base',str(base),'--step','100','--output',str(tmp_path/(name+'.json'))]
        if header_only: command.append('--header-only')
        return subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert run('header',True).returncode == 0
    assert T.load(tmp_path/'header.json')['status'] == 'HEADER_ONLY_NOT_VERIFIED'
    assert run('full',False).returncode == 0
    assert T.load(tmp_path/'full.json')['status'] == 'VERIFIED'
    m = T.load(manifest); m['files'][0]['sha256']='0'*64; T.dump(manifest,m); artifact_update()
    assert run('header_bad_shard_pin',True).returncode == 0
    assert run('full_bad_shard_pin',False).returncode != 0


def test_stage_checker_cpu_command(tmp_path, monkeypatch):
    checker = tmp_path/'sj/orch_cd/legs1_reads/out'; checker.mkdir(parents=True)
    source = Path('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27c/r2/sj/orch_cd/legs1_reads/out')
    for name in M.CHECKER_PINS: (checker/name).write_bytes((source/name).read_bytes())
    T.dump(tmp_path/'bootstrap/CONFIG.json',dict(spec=dict(models=dict(base=dict(path='/logical/base')))))
    receipt = tmp_path/'receipt'; receipt.mkdir()
    seen = []
    def command(root, config, script, args, **kwargs):
        seen.append((script,args,kwargs))
        T.dump(receipt/'CHECK.json',dict(status='HEADER_ONLY_NOT_VERIFIED',step=100))
        return ['/bin/true']
    monkeypatch.setattr(T,'ns_command',command)
    monkeypatch.setattr(T,'environment',lambda root:{})
    result = M.run_export_checker(tmp_path,'/logical/artifact.json','a'*64,100,False,receipt,'/usr/bin/bwrap')
    assert result['status'] == 'HEADER_ONLY_NOT_VERIFIED'
    assert seen[0][0] == M.CHECKER and '--header-only' in seen[0][1]
    assert seen[0][2]['gpu'] is False and seen[0][2]['llguidance_stub'] is False


@pytest.mark.parametrize('family', T.FAMILIES)
def test_full_d0_binding_in_fresh_cpu_process(tmp_path, family):
    script = '''
import sys
from pathlib import Path
import trinity_read as T
import paired_read as P
sys.path.insert(0,str(T.KIT/'proof'))
import fakes
fakes.install()
import namespace_worker as W
import milestone as M
config=T.load(T.REFERENCE/'CONFIG.json')
artifact=dict(kind='c1_export',path=str(T.FSW/'ap/8865619b/runs/359fcc3c/m100/artifact.json'),sha256='a'*64)
config['spec']['artifact']=artifact
config['spec']['models']['cp1m200']=artifact.copy()
config['spec']['step']=100
runtime=Path('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27c/r2/sj/orch_cd')
_,_,_,_,dest,cfg,tasks,_,report=W.bind_plan(config,sys.argv[1],Path(sys.argv[2]),
    reader=runtime/'legs1_reads',kit=runtime/'rv_merge_fix/work/r3/aws_vl64rt',camera=T.physical(T.DEFAULT_ROOT,P.CAMERA))
M.validate_membership(sys.argv[1],report['ids'])
assert cfg['legs1']['artifact']['path']==artifact['path']
assert cfg['legs1']['step']==100 and cfg['build_only']
'''
    result = subprocess.run([sys.executable,'-B','-c',script,family,str(tmp_path/family)],
                            cwd=str(T.BUILD),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    assert result.returncode == 0, result.stdout+result.stderr
    assert T.load(tmp_path/family/'NEED.json')['items'] == len(M.inventory()[family]['items'])
