"""Collect bounded H evidence, including exact reconstructable deliveries."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
from build_support import read_tar,write_tar
HERE=Path(__file__).resolve().parent
A4=Path('/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A4')
sha=lambda b:hashlib.sha256(b).hexdigest()
def zipbytes(raw):
    f=io.BytesIO()
    with gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as z:z.write(raw)
    return f.getvalue()
def index():
    ev=HERE/'evidence';paths=sorted(p for p in HERE.rglob('*') if p.is_file() and p!=ev/'INDEX.md' and '__pycache__' not in p.parts)
    assert all(p.stat().st_size<5000000 for p in paths)
    size=sum(p.stat().st_size for p in paths if ev in p.parents)
    assert size<12000000,size
    text=('This evidence reconstructs both H deliveries in memory. Run `/usr/bin/python3 -B review_h.py`; no `/dev/shm`, source workspace, network, extraction or third-party package is needed.\n'
          'Concatenate A4/1.tgz.part0 and part1 for the authenticated A4 source. Each H directory supplies payload and delivery deltas plus BUILD.json.\n'
          'Paths beginning `../` are workspace code, bindings and frozen inputs. Test results describe local CPU and synthetic checks; no Orchard jobs were submitted.\n'
          'All SHA256 values cover exact stored bytes. INDEX.md is the index itself and is excluded from its own digest.\n\n'
          'Evidence bytes excluding this index: %d.\n\n| File | Bytes | SHA256 |\n|---|---:|---|\n'%size)
    for p in paths:
        rel=str(p.relative_to(ev)) if ev in p.parents else '../'+str(p.relative_to(HERE))
        text+='| `%s` | %d | `%s` |\n'%(rel,p.stat().st_size,sha(p.read_bytes()))
    (ev/'INDEX.md').write_text(text)
    assert size+(ev/'INDEX.md').stat().st_size<12000000
    print(json.dumps(dict(evidence_bytes=size+(ev/'INDEX.md').stat().st_size,indexed_files=len(paths))))
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args();w=Path(a.work);ev=HERE/'evidence';ev.mkdir(exist_ok=True)
    def put(n,raw):
        assert len(raw)<5000000,n
        p=ev/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    source=(A4/'1.tgz').read_bytes();assert sha(source)=='dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459'
    for i,start in enumerate(range(0,len(source),3000000)):put('A4/1.tgz.part%d'%i,source[start:start+3000000])
    before=dict((m.name,d) for m,d in read_tar(source));oldpf=dict((m.name,d) for m,d in read_tar(before['0.tgz']))
    for step in (200,544):
        sw=w/str(step);report=json.loads((sw/'stage/BUILD.json').read_text())['H'];delivery=(Path(report['delivery_dir'])/'1.tgz').read_bytes()
        assert sha(delivery)==report['delivery_sha256'];members=read_tar(delivery);nf=dict((m.name,d) for m,d in members)
        pf=read_tar(nf['0.tgz'])
        put('H%d/payload_delta.tgz'%step,write_tar([(m,d) for m,d in pf if oldpf.get(m.name)!=d]))
        put('H%d/delivery_delta.tgz'%step,write_tar([(m,d) for m,d in members if m.name!='0.tgz' and before.get(m.name)!=d]))
        for n in ('BUILD.json','DIFF.txt'):put('H%d/'%step+n,(sw/'stage'/n).read_bytes())
        put('H%d/PLANNING.json'%step,(sw/'PLANNING.json').read_bytes())
    for n in ['TEST_RESULTS.json','SCORE_RESULTS.json','PLACE_RESULTS.json']:put(n,(w/n).read_bytes())
    put('SCRIPT_RESULTS.json',Path('/dev/shm/c18h/script_tests.log').read_bytes())
    sources=[]
    for i,s in enumerate(json.loads((HERE/'TIMING_H.json').read_text())['sources']):
        raw=Path(s['path']).read_bytes();assert sha(raw)==s['sha256'];dest='timing/camera%d.jsonl.gz'%i;put(dest,zipbytes(raw));sources.append(dict(s,evidence=dest,source_bytes=len(raw)))
    put('SOURCES.json',(json.dumps(sources,sort_keys=True,indent=2)+'\n').encode())
    references=[(HERE.parent/'ebuild'/n) for n in ['build_e.py','score_e.py','place_fill_e.py','o_cpu_E.sh','o_sub_E.sh','test_e.py']]
    references += [(HERE.parent/'dbuild'/n) for n in ['build_d.py','place_fill_d.py','bind_D200.json','bind_D544.json','generate_scripts_d.py']]
    references += [Path('/scratch/jjyeung/orch_n30/cont_ops17/work/build_r10.py'),Path('/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/bases/b1/export_544.json')]
    for p in references:put('reference/'+p.name,p.read_bytes())
    index()
if __name__=='__main__':main()
