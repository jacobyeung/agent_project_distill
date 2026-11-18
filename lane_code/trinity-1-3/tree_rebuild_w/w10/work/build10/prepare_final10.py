from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build10';F=L.parent/'w9f'
for rel in ('work/build5/proofs/suite_tree/results.json','work/build5/proofs/suite_tree/source_hashes.json'):
    source=F/rel;target=L/rel
    if source.exists() and not target.exists():
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
source=L.parent/'work/build9/kits/RESULTS.json'
(B/'INHERITED_KITS.json').write_bytes(source.read_bytes())
p=B/'stage9.py';s=p.read_text().replace("L.parent/'work/build9/kits/RESULTS.json'","B/'INHERITED_KITS.json'");p.write_text(s)
p=B/'make_delivery.py';s=p.read_text().replace('tree_rebuild_b9f_','tree_rebuild_b10_')
s=s.replace("members=list(dict.fromkeys(members))", "members.extend(p for p in (B/'eat1').rglob('*') if p.is_file() and p.suffix in ('.py','.json'))\nmembers=list(dict.fromkeys(members))")
p.write_text(s)
p=B/'seal.py';p.write_text(p.read_text().replace('build9-tree-seal-v1','build10-tree-seal-v1'))
checks=[]
for name in ('run.sh','seal.py','stage9.py','make_delivery.py','package.py','packet_final.py','PACKET_TEST.sh',
             'PACKAGE_TEST.sh','proof_forward9.py','proof_parity_numeric10.py','test_runner.py','compact_tmp.py'):
    p=B/name
    checks.append(dict(path=str(p.relative_to(L)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                       output_root='L inferred from __file__ or explicit TMPDIR; packet fixtures rooted at proofs/packet'))
(B/'EXECUTABLE_PATH_SEARCH.json').write_text(json.dumps(checks,indent=2)+'\n')
print('Final harness paths prepared; source seal and kits pending.')
