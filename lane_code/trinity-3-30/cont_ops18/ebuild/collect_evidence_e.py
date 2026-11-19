"""Copy bounded, independently reviewable evidence into this workspace."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
from build_support import read_tar

HERE=Path(__file__).resolve().parent
A4=Path('/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A4')
BASE544=Path('/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3s/bases/b1/work/ret')
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--followup',required=True);a=p.parse_args()
    w=Path(a.work);ev=HERE/'evidence';ev.mkdir(exist_ok=True)
    def put(name,raw):
        assert len(raw)<5000000,name
        path=ev/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    source=(A4/'1.tgz').read_bytes();assert sha(source)=='dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459'
    for i,start in enumerate(range(0,len(source),3000000)):put('A4/1.tgz.part%d'%i,source[start:start+3000000])
    report=json.loads((w/'stage/BUILD.json').read_text())['E']
    delivery=(Path(report['delivery_dir'])/'1.tgz').read_bytes();assert sha(delivery)==report['delivery_sha256']
    files=dict((m.name,d) for m,d in read_tar(delivery));payload=dict((m.name,d) for m,d in read_tar(files['0.tgz']))
    for n,d in files.items():
        if n!='0.tgz':put('E/delivery/'+n,d)
    put('E/payload/9.json',payload['9.json'])
    put('scoring/items/devs1_routed.json',payload['items/devs1_routed.json'])
    put('scoring/h1eval/scorers.py',payload['h1eval/scorers.py'])
    for name in ('TEST_RESULTS.json','PLANNING.json','SCORES.json'):put(name,(w/name).read_bytes())
    for name in ('BUILD.json','DIFF.txt'):put('E/'+name,(w/'stage'/name).read_bytes())
    put('SCRIPT_RESULTS.json',(Path(a.followup)/'FOLLOWUP_RESULTS.json').read_bytes())
    put('RELEASE_RESULTS.json',Path('/dev/shm/c18e/RELEASE_RESULTS.json').read_bytes())
    sources=[]
    for label,root,rd in [('A4_return',A4/'ret',0),('step544_return',BASE544,1)]:
        rel='metadata/reads/%d/metadata/journals/3/0'%rd
        for n in ('environment.json','items.jsonl'):
            path=root/rel/n;raw=path.read_bytes();name=label+'/'+rel+'/'+n
            if n.endswith('jsonl'):
                buf=io.BytesIO()
                with gzip.GzipFile(fileobj=buf,mode='wb',mtime=0) as f:f.write(raw)
                put(name+'.gz',buf.getvalue());dest=name+'.gz'
            else:put(name,raw);dest=name
            sources.append(dict(source=str(path),evidence=dest,source_bytes=len(raw),source_sha256=sha(raw)))
    excerpts={}
    for n,lo,hi in [('tree/student_pilot/students.py',1,22),('tree/student_pilot/carrier_c1_run.py',501,509),
                    ('b/parity_kit/stage_restore.py',12,29),('tree/student_pilot/carrier_c1_run.py',2051,2060),
                    ('tree/student_pilot/decoupled_v.py',43,65)]:
        raw=payload[n];excerpts[n]=dict(sha256=sha(raw),first_line=lo,last_line=hi,text='\n'.join(raw.decode().splitlines()[lo-1:hi]))
    basis=dict(base_identity='c202236235762e1c871ad0ccb60c8ee5ba337b9a',
               definition='Original Qwen/Qwen3.5-9B snapshot revision; model provenance is checked against the base manifest, while the artifact run, step and config identity are separate fields.',
               runtime_confirmation='place_fill_e verifies hash-pinned D0 config base_identity; a/4.py checks artifact identity against config and sealed export_binding.',
               excerpts=excerpts)
    put('BASE_IDENTITY.json',(json.dumps(basis,sort_keys=True,indent=2)+'\n').encode())
    put('SOURCES.json',(json.dumps(sources,sort_keys=True,indent=2)+'\n').encode())
    index(ev)


def index(ev):
    paths=sorted(p for p in ev.rglob('*') if p.is_file() and p.name!='INDEX.md')
    total=sum(p.stat().st_size for p in paths);assert total<10000000,total
    text=('Reviewer evidence is self-contained. `python3 -B review_e.py` reconstructs A4 and E in memory and verifies their hashes.\n'
          'A4/1.tgz.part0 + part1 concatenate to the authenticated source delivery; split files meet the 5 MB cap.\n'
          'E/delivery contains every delivery member except 0.tgz; rebuild it from A4 payload members and E/payload/9.json.\n'
          'The two *.jsonl.gz files decompress byte-for-byte to the supplied baseline journals. SOURCES.json records their original hashes.\n'
          'PLANNING and test results are local evidence; no export restore or Orchard CPU/GPU job was run.\n\n'
          'Indexed bytes: %d. SHA256 covers exact stored bytes.\n\n| File | Bytes | SHA256 |\n|---|---:|---|\n'%total)
    for p in paths:text+='| `%s` | %d | `%s` |\n'%(p.relative_to(ev),p.stat().st_size,sha(p.read_bytes()))
    (ev/'INDEX.md').write_text(text)
    workspace=[p for p in HERE.rglob('*') if p.is_file()]
    assert all(p.stat().st_size<5000000 for p in workspace)
    total_all=sum(p.stat().st_size for p in workspace);assert total_all<10000000,total_all
    print(json.dumps(dict(evidence_files=len(paths)+1,evidence_bytes=total+(ev/'INDEX.md').stat().st_size,workspace_bytes=total_all)))

if __name__=='__main__':main()
