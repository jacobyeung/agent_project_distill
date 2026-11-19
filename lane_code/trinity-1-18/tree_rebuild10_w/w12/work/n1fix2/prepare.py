from pathlib import Path
import json,hashlib,re
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
local_by_sha={sha(p):p for p in (B/'inputs').glob('*.json')}
prefixes=['/scratch/jjyeung/orch_n30/tree_rebuild_w/w12','/scratch/jjyeung/orch_n30/tree_rebuild_w/w12','/scratch/jjyeung/orch_n30/tree_rebuild_w/w12','/scratch/jjyeung/orch_n30/tree_rebuild_w/w12']
def localize(v):
    if isinstance(v,dict):
        if v.get('sha256') in local_by_sha and 'path' in v:
            return dict(v,path=str(local_by_sha[v['sha256']]))
        return {k:localize(x) for k,x in v.items()}
    if isinstance(v,list):return [localize(x) for x in v]
    if isinstance(v,str):
        if v.startswith(str(L)+'/'):return v
        for old in prefixes:
            if v.startswith(old+'/'):
                return (str(L)+v[len(old):]).replace('/work/n1fix/','/work/n1fix2/')
    return v
for p in (B/'inputs').glob('*.json'):
    try:value=json.loads(p.read_text())
    except json.JSONDecodeError:continue
    new=localize(value)
    if new!=value:p.write_text(json.dumps(new,indent=2)+'\n')
def refresh(v):
    if isinstance(v,dict):
        result={k:refresh(x) for k,x in v.items()}
        if 'path' in result and 'sha256' in result:
            p=Path(result['path'])
            if p.is_relative_to(L) and p.is_file():result['sha256']=sha(p)
        return result
    if isinstance(v,list):return [refresh(x) for x in v]
    return v
for _ in range(4):
    for p in (B/'inputs').glob('*.json'):
        try:value=json.loads(p.read_text())
        except json.JSONDecodeError:continue
        new=refresh(value)
        if new!=value:p.write_text(json.dumps(new,indent=2)+'\n')
rows=json.loads((B/'PACKET_INPUTS.json').read_text())
for row in rows:
    source=L/row['target'].replace('work/n1fix2/','work/n1fix/')
    assert sha(source)==row['sha256'],source
    target=L/row['target'];target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():target.symlink_to(source)
    row['source']=str(source.relative_to(L))
(B/'PACKET_INPUTS.json').write_text(json.dumps(rows,indent=2))
p=B/'make_delivery.py';p.write_text(p.read_text().replace('tree_rebuild_bn1f_','tree_rebuild_bn1f2_'))
p=B/'mutations.py';s=p.read_text().replace('from student_pilot import r1_training,scene_division_gate','from student_pilot import r1_training,scene_division_gate,r1_handover\nfrom tests.test_r2_n1fix2 import Confirmation')
s=s.replace('results=[]', '''cases.extend([
 ('H2',r1_handover,"bound.get('config_sha256') != identity or ",'','test_H2_binding_config'),
 ('H6',r1_handover,"identity != artifact.get('config_sha256') or ",'','test_H6_artifact_config')])
results=[]''')
s=s.replace("clean=unittest.TextTestRunner", "Test=Confirmation if name.startswith('H') else N1Fix\n    clean=unittest.TextTestRunner").replace('run(N1Fix(test))','run(Test(test))')
s=s[:s.index("(B/'STATUS.md').write_text")]+"print(json.dumps([{k:r[k] for k in ('mutant','clean_pass','caught')} for r in results]))\n"
p.write_text(s)
names=['run.sh','test_runner.py','compact_tmp.py','stage9.py','monitor9.py','proof_text.py','proof_forward9.py','seal.py','make_delivery.py','package.py','packet_final.py','PACKET_TEST.sh','PACKAGE_TEST.sh','requalification_gate.py','mutations.py']
issues=[]
for name in names:
    for number,line in enumerate((B/name).read_text().splitlines(),1):
        if 'L.parent' in line or '/tree_rebuild_w/w9' in line or '/tree_rebuild/' in line:issues.append([name,number,line])
(B/'EXECUTABLE_PATH_SEARCH.json').write_text(json.dumps(dict(files=names,issues=issues),indent=2))
assert not issues
(B/'STATUS.md').write_text('N1a, N1b and N1c are implemented. H2/H6 regression tests pass on clean code. N3 normalization and independent reader, and N5 path and empty-directory guards are implemented. Targeted verification found two obsolete fixtures; they are corrected. Final suites and mutation run are pending. Evidence: proofs/targeted/results.json.\n')
print('Local inputs, packet references and executable path search prepared.')
