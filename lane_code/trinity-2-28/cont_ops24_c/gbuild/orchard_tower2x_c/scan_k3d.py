"""Scan shipped code, decoded transport and every diagnostic output surface."""
import ast
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'orchard_tower2x_b'
spec=importlib.util.spec_from_file_location('oldscan',OLD/'scan.py')
prior=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
scan=prior.scan


def main():
    build=json.loads((ROOT/'BUILD.json').read_text())
    checked=[]
    def inspect(name,raw,exception=None):
        hits=scan(raw.decode('latin1'))
        checked.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                            hits=hits,exception=exception))
        if not exception:
            assert not hits,(name,hits)
    for name in build['small_files']:
        raw=(ROOT/name).read_bytes()
        if name=='1.json':
            cfg=json.loads(raw)
            original=json.loads((OLD/name).read_text())
            original.update(x0=build['token'],xl=build['path']+'/8')
            assert cfg==original
            inspect(name,raw,'Only inherited configuration values; token and frame root changed.')
        else:
            inspect(name,raw)
        if name.endswith('.py'):
            compile(raw,name,'exec')
        if name.endswith('.sh'):
            subprocess.run(['bash','-n',str(ROOT/name)],check=True)
    script=(ROOT/'o_place.sh').read_text()
    body=script.split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
    tree=ast.parse(body)
    call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
              and n.func.attr=='b64decode')
    encoded=ast.literal_eval(call.args[0])
    blob=base64.b64decode(encoded,validate=True)
    inspect('o_place.sh',script.encode(),'Embedded compressed bytes audited after decoding.')
    inspect('o_place.sh:text',script.replace(encoded,'').encode())
    with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as archive:
        assert set(archive.getnames())==set(build['small_files'])
        for item in archive:
            assert item.isfile() and archive.extractfile(item).read()==(ROOT/item.name).read_bytes()
    for name in ('o_place.sh','o_cpu.sh','o_check_sub.sh','o_fetch.sh'):
        raw=(ROOT/name).read_bytes()
        if name!='o_place.sh':
            inspect(name,raw.replace(b'--exclude=orchard-community-4',b''))
        subprocess.run(['bash','-n',str(ROOT/name)],check=True)
    for name,prefix in (('o_cpu.sh','4'),('o_check_sub.sh','5')):
        text=(ROOT/name).read_text()
        assert '--mem=200G' in text and '--cpus-per-task=8' in text
        assert '--exclude=orchard-community-4' in text and 'test -z "$q"' in text
        assert text.index('test -z "$q"') < text.index('reply=')
        assert '--output="$P/'+prefix+'.out"' in text
        assert '--error="$P/'+prefix+'.stderr"' in text
        assert '/dev/null' not in text
    cpu=json.loads((ROOT/'CPU_K3D.json').read_text())
    work=Path(cpu['work'])
    logs=[work/'9.err',work/'e0/4.err',work/'e1/5.err',work/'f/4.err']
    for path in logs:
        raw=path.read_bytes()
        inspect(str(path.relative_to(work)),raw)
        assert len(raw)<=16384
        for line in raw.splitlines():
            record=json.loads(line)
            assert re.fullmatch('E[0-9]{2}',record['code'])
            for frame in record['files']:
                assert re.fullmatch(r'(?:[029]|[0-9a-f]{16})\.py:[0-9]+',frame)
    inspect('stream summaries',json.dumps(cpu['opaque_stream_summaries']).encode())
    for name in ('4.out','4.stderr'):
        inspect(name,(work/'f'/name).read_bytes())
    # Exhaust the diagnostic type/code alphabet, including hostile payload text.
    spec=importlib.util.spec_from_file_location('diag',ROOT/'9.py')
    diag=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diag)
    for cls in (ValueError,TypeError,KeyError,RuntimeError,TimeoutError,OSError,FileNotFoundError,
                PermissionError,MemoryError,ImportError,ModuleNotFoundError,AssertionError,
                type('camera_tower_error',(Exception,),{})):
        try:
            raise cls('/payload/arkit/tower.py: secret source text')
        except Exception as exc:
            inspect('diagnostic '+cls.__name__,json.dumps(diag.detail(exc)).encode())
    for code in range(100):
        inspect('code '+str(code),json.dumps(diag.detail(ValueError('E'+str(code).zfill(2)))).encode())
    oldscan=json.loads((OLD/'SCAN_K3c.json').read_text())
    assert oldscan['passed'] and oldscan['png_count']==630
    prior_archive=next(x for x in oldscan['files'] if x['file']=='8.tgz')
    assert prior_archive['sha256']==build['reused_sha256']
    with (OLD/'8.tgz').open('rb') as f:
        assert hashlib.file_digest(f,'sha256').hexdigest()==build['reused_sha256']
    report=dict(passed=True,files=checked,unapproved_text_hits=[],
        reused_png_scan=dict(sha256=build['reused_sha256'],png_count=630,
                            evidence_sha256=hashlib.sha256((OLD/'SCAN_K3c.json').read_bytes()).hexdigest()),
        diagnostics='Exception type (unknown types hex encoded), E-code, opaque file:line only; output streams summarized by byte count/SHA256.',
        exceptions=['Unchanged inherited configuration values.','Required excluded-node literal.',
                    'Compressed transport audited by exact decoded member comparison.'])
    (ROOT/'SCAN_K3D.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checked=len(checked),unapproved_text_hits=[])))


if __name__=='__main__':main()
