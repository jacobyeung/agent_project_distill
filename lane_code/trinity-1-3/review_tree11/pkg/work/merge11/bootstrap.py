from pathlib import Path
import hashlib, json, difflib
L=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/wm')
N=L.parent; T=N/'w10'; F=N/'w9f'; G=N/'wn2'; B=L/'work/merge11'
B.mkdir(exist_ok=True); (L/'work/tmp').mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base={line.split(maxsplit=1)[1].strip().removeprefix('./'):line.split()[0] for line in (F/'out/TREE_FILES.sha256').read_text().splitlines()}
def inventory(root): return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
def changes(v): return {'added':sorted(v.keys()-base.keys()),'changed':sorted(k for k in v.keys()&base.keys() if v[k]!=base[k]),'removed':sorted(base.keys()-v.keys())}
ti=inventory(T/'work/tree_r1'); gi=inventory(L/'work/tree_r1')
tc=changes(ti); gc=changes(gi)
ts=set(sum(tc.values(),[])); gs=set(sum(gc.values(),[]))
v={'base_inventory':str(F/'out/TREE_FILES.sha256'),'build10':tc,'n1fix2':gc,'intersection':sorted(ts&gs),'build10_hashes':{k:ti.get(k) for k in ts},'n1fix2_hashes':{k:gi.get(k) for k in gs}}
(B/'CHANGESETS.json').write_text(json.dumps(v,indent=2)+'\n')
(B/'STATUS.md').write_text('# Build 11 status\n\nStep 1 complete. Hash change sets are recorded in CHANGESETS.json. GO=false. Merge and qualification remain pending.\n')
(B/'DECISIONS.md').write_text('# Decisions\n\n- Legacy exports: options are config-bound buffer migration or an explicit named refusal. Default: named refusal for exports lacking fixed-readout buffers; test the real export producer and reader. The training init path remains unchanged.\n- Missing bound parity operands and frame-64 reader qualification remain blockers. No fabricated operands or expanded scope.\n- Proof outputs use fixed folders and overwrite owned files. Existing source evidence is read-only.\n')
assert not tc['removed'], tc['removed']
for rel in sorted(ts-gs):
    p=L/'work/tree_r1'/rel; p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((T/'work/tree_r1'/rel).read_bytes())
for rel in sorted(ts&gs):
    old=(F/'work/tree_r1'/rel).read_text().splitlines(True)
    for tag,root in [('build10',T),('n1fix2',G)]:
        patch=''.join(difflib.unified_diff(old,(root/'work/tree_r1'/rel).read_text().splitlines(True),fromfile='base/'+rel,tofile=tag+'/'+rel))
        (B/(tag+'_'+Path(rel).name+'.patch')).write_text(patch)
print(json.dumps(v,indent=2))
