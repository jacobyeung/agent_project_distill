"""Verify the complete E evidence without /dev/shm, extraction or third-party packages."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
from build_support import read_tar,write_tar,bundle_of
import score_e

HERE=Path(__file__).resolve().parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
read=lambda path:json.loads(path.read_text())


def main():
    ev=HERE/'evidence'
    for line in (ev/'INDEX.md').read_text().splitlines():
        if not line.startswith('| `'):continue
        fields=line.split('|');path=ev/fields[1].strip().strip('`')
        assert path.stat().st_size==int(fields[2]),path
        assert sha(path.read_bytes())==fields[3].strip().strip('`'),path
    source=b''.join((ev/'A4'/('1.tgz.part%d'%i)).read_bytes() for i in range(2))
    assert sha(source)=='dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459'
    orig=read_tar(source);files=dict((m.name,d) for m,d in orig)
    oldpay=read_tar(files['0.tgz']);pfd=dict((m.name,d) for m,d in oldpay)
    newpay=[(m,(ev/'E/payload/9.json').read_bytes() if m.name=='9.json' else d) for m,d in oldpay]
    rebuilt=write_tar(newpay);newfiles={n:(rebuilt if n=='0.tgz' else (ev/'E/delivery'/n).read_bytes()) for n in files}
    public=json.loads(newfiles['0.json']);pk=json.loads(newfiles['PACKAGE.json']);plan=json.loads((ev/'E/payload/9.json').read_text())
    report=read(ev/'E/BUILD.json')['E']
    assert sha(rebuilt)==public['payload_sha256']==report['payload_sha256']
    assert sha(write_tar([(m,newfiles[m.name]) for m,d in orig]))==report['delivery_sha256']
    assert public['token']==pk['token']==plan['token']==report['token']
    assert sha(json.dumps(plan,sort_keys=True,separators=(',',':')).encode())==public['plan_sha256']
    for n,h in pk['files'].items():assert sha(newfiles[n])==h,n
    assert sha((HERE/'bind_E200.json').read_bytes())==report['binding_sha256']
    assert plan['export_binding']=={k:read(HERE/'bind_E200.json')[k] for k in plan['export_binding']}
    for n,pin in plan['payload_pins'].items():assert pin==dict(bytes=len(pfd[n]),sha256=sha(pfd[n])),n
    assert pfd['items/devs1_routed.json']==(ev/'scoring/items/devs1_routed.json').read_bytes()
    assert pfd['h1eval/scorers.py']==(ev/'scoring/h1eval/scorers.py').read_bytes()
    bundle=dict((m.name,d) for m,d in read_tar(bundle_of(newfiles['BATCH.sh'])[1]))
    assert bundle['0.json']==newfiles['0.json'] and bundle['7.py']==newfiles['a/6.py']
    for n,info in read(ev/'BASE_IDENTITY.json')['excerpts'].items():
        assert sha(pfd[n])==info['sha256']
        assert '\n'.join(pfd[n].decode().splitlines()[info['first_line']-1:info['last_line']])==info['text']
    for spec in read(ev/'SOURCES.json'):
        path=ev/spec['evidence'];raw=path.read_bytes()
        if path.suffix=='.gz':raw=gzip.decompress(raw)
        assert len(raw)==spec['source_bytes'] and sha(raw)==spec['source_sha256']
    line=next(l for l in (HERE/'o_build_E.sh').read_text().splitlines() if l.startswith('assets = '))
    assets=ast.literal_eval(line.split('=',1)[1].strip())
    for n,spec in assets.items():
        raw=gzip.decompress(base64.b64decode(spec['data']))
        assert sha(raw)==spec['sha256'] and raw==(HERE/('build_e.py' if n=='b.py' else n)).read_bytes(),n
    value,items=score_e.manifest(ev/'scoring/items/devs1_routed.json');records=score_e.scorer_records(ev/'scoring')
    a,ar=score_e.evaluate(ev/'A4_return',value,items,records)
    b,br=score_e.evaluate(ev/'step544_return',value,items,records,1)
    selfdiff=score_e.comparison(a,a,items,records)
    assert all(v['value']==0 and v['ci95']==[0,0] for g in selfdiff.values() for v in g.values())
    expected=read(ev/'SCORES.json')
    assert ar['groups']==expected['current']['groups']
    assert br['groups']==expected['baselines']['step544']['groups']
    assert score_e.comparison(a,b,items,records)==expected['current_minus_step544']
    print(json.dumps(dict(passed=True,token=public['token'],delivery_sha256=report['delivery_sha256'],
          self_comparison_zero=True,paired_items=len(a),source_members=len(files),payload_members=len(pfd),
          evidence_self_contained=True),sort_keys=True,indent=2))

if __name__=='__main__':main()
