"""Build deterministic source, payload and family artifacts without network access."""
from pathlib import Path
import sys,tarfile,difflib,json
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *
import engine

def archive(root,target):
    with tarfile.open(target,'w') as t:
        for p in sorted(root.rglob('*')):
            if not p.is_file():continue
            name=str(p.relative_to(root));info=tarfile.TarInfo(name);info.size=p.stat().st_size;info.mtime=0;info.mode=p.stat().st_mode&0o777
            with p.open('rb') as stream:t.addfile(info,stream)

def diff(root,target):
    patch=[];files=[]
    scorers={}
    for p in sorted((B/'code').rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(B/'code');old=root/rel
        if p.name in ('s0.py','s1.py','s2.py','s3.py'):
            scorers[str(rel)]=pin(p);continue
        if old.is_file() and old.read_bytes()==p.read_bytes():continue
        lines=list(difflib.unified_diff(old.read_text().splitlines(True) if old.is_file() else [],p.read_text().splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
        patch.extend(lines);files.append(dict(file=str(rel),added=sum(x.startswith('+') and not x.startswith('+++') for x in lines),removed=sum(x.startswith('-') and not x.startswith('---') for x in lines)))
    target.write_text(''.join(patch));return dict(files=files,added=sum(x['added'] for x in files),removed=sum(x['removed'] for x in files),scorers=scorers)

# Reference bundle includes original arrays and only the small read metadata.
ref=B/'work/reference'
for name,source in [('c.json',R/'in/vsti/vstibench_repr_450_v3.json'),('d.json',R/'in/vsti/media.json'),('e.json',B/'out/RELEASE_CHECK.json')]:
    (ref/name).write_bytes(source.read_bytes())
for n,source in [('f.jsonl','f17.per_question_scores.jsonl'),('g.jsonl','p1m200.per_question_scores.jsonl')]:
    (ref/n).write_bytes((R/'in/comparators'/source).read_bytes())
archive(ref,B/'out/d.tar');archive(B/'code',B/'out/c.tar')
stats={}
for name,root in [('V1b',B.parent/'02_vsti_b/code'),('C8R',R/'work/c8r/code')]:stats[name]=diff(root,B/('out/DIFF_vs_'+name+'.patch'))
dump(B/'out/DIFF_STATS.json',stats)
parent=load(R/'work/c8r/FAMILY.json');config=load(ref/'metadata/CONFIG.json')
# Existing asset names and generation pins are preserved exactly from the accepted packet.
family=dict(schema='camera-read-family-v1',parent=pin(R/'work/c8r/FAMILY.json'),parent_code=pin(R/'work/c8r/code_c8r.tar'),parent_config=config,
    code=pin(B/'out/c.tar'),code_sources=engine.source_pins(),synthetic=False,launch_ready=False,
    limits=parent['limits'],protocol=dict(served=['move','turn','pose'],arms=['native','scripted_camera'],refusal='error: call_unavailable; answer directly from the video'),
    inputs=dict(keys=load(B/'out/CANARY_KEYS.json')['canary']+load(B/'out/CANARY_KEYS.json')['post_canary'],item_sha256=sha(R/'in/vsti/vstibench_repr_450_v3.json'),media_sha256=sha(R/'in/vsti/media.json')),
    added={k:dict(path='/project/community/jjyeung/okh7/d9c35d0a/'+k+'.tar',name='q8/d9c35d0a/'+k+'.tar',
                 sha256=sha(B/('out/'+k+'.tar')) if k in 'cd' else None,bytes=(B/('out/'+k+'.tar')).stat().st_size if k in 'cd' else None,
                 generation=None,verified=False) for k in 'abcd'},
    tower_members={},deadline_utc='2026-11-16T16:15:00Z',proof_keys=load(B/'out/PROOF_KEYS.json'),
    blockers=['Tower and full-frame archive upload receipts are pending.','New archive GCS generations and second-copy SHA checks are pending.','GPU preparation/proof/decode and remote staging/returns have not run.'])
import ast
source=ast.parse((R/'from113/work/tree/student_pilot/tower_read.py').read_text())
values={n.targets[0].id:ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('WEIGHTS_SHA256','CONFIG_SHA256')}
family['tower_members']={'model.safetensors':values['WEIGHTS_SHA256'],'config.json':values['CONFIG_SHA256']}
family.update(packet_root='/project/community/jjyeung/okh7/d9c35d0a/p/<token>/',return_reserve_seconds=600,report_venue='local',review_items=['F1','F2','F3','S1','S2','S3','S4','S5','S6','S7','S8'])
dump(B/'out/FAMILY.json',family);dump(B/'out/ADDITIONS.pending.json',family['added'])
dump(B/'out/PACKAGE.json',dict(code=pin(B/'out/c.tar'),family=pin(B/'out/FAMILY.json'),reference=pin(B/'out/d.tar'),diff=stats,launch_ready=False))
# Name the copied scorer authority separately; byte equality is checked, not asserted by filename.
names={'s0.py':'score_and_aggregate.py','s1.py':'scoring.py','s2.py':'_score_index_vstibench_mechanical.py','s3.py':'score_record_core.py'}
rows=[]
for target,source in names.items():
    assert (B/'code'/target).read_bytes()==(R/'in/scorer'/source).read_bytes()
    rows.append(dict(copy=target,source=str(R/'in/scorer'/source),sha256=sha(B/'code'/target),byte_identical=True))
dump(B/'out/SCORER_COPIES.json',rows)
print(json.dumps({k:v for k,v in load(B/'out/PACKAGE.json').items() if k!='diff'},indent=2))
