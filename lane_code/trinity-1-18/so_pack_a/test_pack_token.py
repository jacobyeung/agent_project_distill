"""Additive adapter regression; execute beside native build_d.py or build_r10.py."""
import ast, base64, gzip, hashlib, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pack_token

def main():
    here=Path(__file__).resolve().parent
    kind='d' if (here/'build_d.py').is_file() else 'r10';source=here/('build_d.py' if kind=='d' else 'build_r10.py');raw=source.read_text()
    assert pack_token.adapted(raw,kind,None,False)==raw
    changed=pack_token.adapted(raw,kind,'a123456789abc',True);compile(changed,str(source),'exec');assert changed!=raw
    for bad in ('0123456789ab','MODEL','a123'):
        try:pack_token.adapted(raw,kind,bad,True)
        except ValueError:pass
        else:raise AssertionError('Accepted invalid token')
    result=dict(passed=True,kind=kind,default_off_source_identical=True,native_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    if kind=='d':
        script=(here/'o_build_D.sh').read_text();assets=ast.literal_eval(next(l for l in script.splitlines() if l.startswith('assets = ')).split('=',1)[1].strip());embedded=gzip.decompress(base64.b64decode(assets['b.py']['data']));assert embedded==source.read_bytes();result['embedded_builder_unchanged']=True
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
