"""Authenticate scanner inventories for this kit and compare its upload set to 21e."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build22';B=L/'work/build21';K=D/'kits/q'
sys.path[:0]=[str(D),str(B),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
source=(B/'naming21.py').read_text();tree=ast.parse(source)
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE_SEALS' for t in n.targets))
maps={}
for document in ('k/7.json','k/c0.json'):
    value=J.load(K/document)
    for field in ('files','sources','operation_sources'):maps[document,field]=digest(value[field])
lines=source.splitlines();source='\n'.join(lines[:node.lineno-1]+['SOURCE_SEALS='+repr(maps)]+lines[node.end_lineno:])+'\n'
old='u/a4509d8c159f71f81d0f82adad8e85ef8135d17363084e7281fadddea04c9c5c'
bound=J.load(K/'k/c.json')['r1_training']['mix']['path'];source=source.replace(old,bound)
(D/'naming22.py').write_text(source)
spec=importlib.util.spec_from_file_location('naming22',D/'naming22.py');scanner=importlib.util.module_from_spec(spec);spec.loader.exec_module(scanner)
scan=scanner.scan_decoded(K);J.write(D/'SCAN.json',scan)
seal=verify(K);assert seal==J.sha(K/'SHA256SUMS.txt')
before=J.load(L/'attic/build21g/UPLOADS.json');after=J.load(D/'UPLOADS.json')
oldfiles={x['opaque_name']:x for x in before['files']};newfiles={x['opaque_name']:x for x in after['files']}
diff=dict(added=[v for k,v in newfiles.items() if k not in oldfiles],
          changed=[dict(before=oldfiles[k],after=v) for k,v in newfiles.items() if k in oldfiles and (v['sha256'],v['bytes'])!=(oldfiles[k]['sha256'],oldfiles[k]['bytes'])],
          removed=[v for k,v in oldfiles.items() if k not in newfiles])
J.write(D/'UPLOAD_DIFF.json',dict(baseline='build21e UPLOADS.json retained in attic/build21g',**diff))
unchanged={name:J.sha(K/name)==J.sha(B/'kits/q'/name) for name in ('b/z.py','k/j.json')};assert all(unchanged.values())
J.write(D/'KIT_INTEGRITY.json',dict(kit_q_seal=seal,scan=scan['status'],checked_strings=scan['checked_strings'],
    unchanged=unchanged,tree_seal=J.load(L/'out/TREE_SEAL.json')['tree_sha256'],source_inventories={str(k):v for k,v in maps.items()},
    uploads=len(after['files']),upload_bytes=after['total_bytes'],diff_counts={k:len(v) for k,v in diff.items()},
    resolver_boundary='Preserved resolver authenticates milestone 400 only; it cannot resolve the future step-600 publication.'))
print('PASS kit',seal,len(after['files']),after['total_bytes'],{k:len(v) for k,v in diff.items()})
