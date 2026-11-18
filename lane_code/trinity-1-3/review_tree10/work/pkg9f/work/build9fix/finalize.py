"""Verify frozen outputs, record unresolved requirements and render final reports."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix'
def read(path):return json.loads(path.read_text())
def mark(name,status):
    (B/'FINAL_STAGE.json').write_text(json.dumps(dict(stage=name,status=status))+'\n')
def call(name,*args):
    mark(name,'running')
    subprocess.run([sys.executable,'-I','-s','-B',str(B/name),*map(str,args)],check=True)
    mark(name,'complete')
call('proof_p_format.py')
call('phase.py','targeted')
call('monitor_loader.py')
call('proof_extra.py')
mark('packet','running')
subprocess.run([sys.executable,'-I','-s','-B',str(B/'phase.py'),'packet'],check=True)
mark('packet','complete')
call('legacy_guard_proof.py');call('compare.py')
call('coverage_all.py')
sources=[]
for p in (B/'proofs').rglob('source_hashes.json'):
    if (p.parent/'results.json').exists() and (p.parent/'hits.json').exists():sources.append(p.parent)
call('coverage_n1.py',*sorted(sources))
call('inference_inventory.py');call('report_bindings.py')
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
seal=read(L/'out/TREE_SEAL.json');delivery=read(B/'DELIVERY.json');kit=read(B/'KIT_RESULT.json')
assert digest(inventory(L/'work/tree_r1'))==seal['tree_sha256']==delivery['tree_seal']==kit['source_seal']
assert seal['tree_sha256'][:8] in Path(delivery['path']).name
h=hashlib.sha256()
with (L/delivery['path']).open('rb') as f:
    for block in iter(lambda:f.read(1024**2),b''):h.update(block)
assert h.hexdigest()==delivery['sha256']
assert verify(B/'kits/r1')==kit['kit_sha256']
assert read(B/'proofs/package/ARCHIVE.json')['sha256']==delivery['sha256']
packet=read(B/'proofs/packet/results.json');comparison=read(B/'SUITE_COMPARISON.json')
assert packet and all(v['outcome']=='passed' for v in packet.values())
prior=read(L/'work/build9/SUITE_COMPARISON.json')
prior_regressions={v['test'] for v in prior['failures'] if not v['preexisting']}
new_regressions=[v['test'] for v in comparison['failures'] if not v['preexisting'] and v['test'] not in prior_regressions]
assert not new_regressions, 'New regressions require repair before completion: '+repr(new_regressions)
assert comparison['r2_failures']==0, 'R2 failures require repair before completion'
sizes={}
for name,root in [('lane',L),('tmp',L/'work/tmp')]:
    total=0;pending=[root]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for e in entries:
                if e.is_symlink():continue
                if e.is_dir(follow_symlinks=False):pending.append(e.path)
                elif e.is_file(follow_symlinks=False):total+=e.stat(follow_symlinks=False).st_size
    sizes[name]=total
assert sizes['lane']<=7_000_000_000 and sizes['tmp']<=200_000_000
(B/'FINAL_STORAGE.json').write_text(json.dumps(sizes,indent=2)+'\n')
result=dict(status='COMPLETE_WITH_NAMED_BLOCKERS',GO=False,source_seal=seal['tree_sha256'],
            package=delivery,kit=kit,comparison={k:v for k,v in comparison.items() if k!='failures'},
            packet_passed=len(packet),coverage='work/build9fix/N1_CHANGED_COVERAGE.json',storage=sizes,
            no_new_r2_failures=comparison['r2_failures']==0,
            new_regressions=new_regressions,
            blockers='work/build9fix/CARRIED_BLOCKERS.json',review_event='out/RESULT_build_n1.json')
(B/'FINAL_PASS.json').write_text(json.dumps(result,indent=2)+'\n')
call('write_report.py')
print(json.dumps({k:v for k,v in result.items() if k not in ('kit','comparison')}))
