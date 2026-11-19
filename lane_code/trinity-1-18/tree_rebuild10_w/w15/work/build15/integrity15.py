"""Stream-check the delivery without copying model, database or frame assets."""
from pathlib import Path
import json,sys,hashlib,tarfile,shutil
L=Path(__file__).resolve().parents[2];B=L/'work/build15';O=B/'proofs/integrity';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,load,sha256
from launch_r1.build import verify as verify_r1
from launch_r2.build import verify as verify_r2
seal=load(L/'out/TREE_SEAL.json');delivery=load(B/'DELIVERY.json');archive=L/delivery['path']
assert inventory(L/'work/tree_r1')==seal['files']
assert digest(seal['files'])==delivery['tree_seal']==seal['tree_sha256']
assert sha256(archive)==delivery['sha256'] and archive.stat().st_size==delivery['bytes']<150_000_000
kits=load(B/'KIT_RESULT.json')
for name,r in kits.items():assert (verify_r1 if name=='r1' else verify_r2)(B/'kits'/name)==r['kit_sha256']
with tarfile.open(archive,'r:gz') as tar:
    hashes={};sizes={}
    for member in tar:
        assert member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts
        assert member.name not in hashes
        h=hashlib.sha256()
        with tar.extractfile(member) as stream:
            for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
        hashes[member.name]=h.hexdigest();sizes[member.name]=member.size
    for name,h in seal['files'].items():assert hashes['work/tree_r1/'+name]==h
    for name in ('out/BUILD15_REPORT.md','out/DESIGN_RECORD_tree_rebuild_20261115.md','out/TREE_SEAL.json',
                 'work/build15/DELTA_COVERAGE.json','work/build15/proofs/real/RESULT.json','work/build15/KIT_RESULT.json'):
        assert hashes[name]==sha256(L/name)
    for p in (B/'kits').rglob('*'):
        if p.is_file():assert hashes[str(p.relative_to(L))]==sha256(p)
frozen=B/'proofs/final/frozen/work/tree_r1'
if frozen.exists():assert inventory(frozen)==seal['files']
workspace=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
tmp=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
assert workspace<=1_500_000_000 and tmp<=200_000_000 and shutil.disk_usage('/scratch').free>=85*1024**3
result=dict(status='PASS',source_seal=seal['tree_sha256'],delivery=delivery,archive_members=len(hashes),
    unpacked_bytes=sum(sizes.values()),source_and_kits_match=True,report_and_proof_hashes_match=True,
    workspace_bytes=workspace,tmp_bytes=tmp,scratch_free_bytes=shutil.disk_usage('/scratch').free,
    method='Archive members are hashed as streams; no extraction or checkpoint/database/frame copy.')
(O/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
(B/'STATUS.md').write_text('# Build 15 status\n\nBuild 15 is packaged and stream-verified. A/C/Cprime admit; the native opener witness proof and changed-statement coverage pass. GO=false: missing external inputs and the unchanged packet floating-point comparison failure remain qualified. See out/BUILD15_REPORT.md and work/build15/proofs/integrity/RESULT.json.\n')
