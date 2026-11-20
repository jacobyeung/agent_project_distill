"""Deterministic local resealer. No placement, network, or submission."""
import argparse
import ast
import base64
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
WALLTIME = '05:00:00'
sha = lambda b: hashlib.sha256(b).hexdigest()
jd = lambda v: (json.dumps(v, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
canonical = lambda v: sha(json.dumps(v, sort_keys=True, separators=(',',':')).encode())


def read_tar(raw):
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as t:
        members = t.getmembers()
        if len(members) != len({m.name for m in members}): raise ValueError('duplicate member')
        for m in members:
            if not m.isfile() or m.name.startswith('/') or '..' in Path(m.name).parts:
                raise ValueError('unsafe member')
        return [(m, t.extractfile(m).read()) for m in members]


def added(name, data):
    m = tarfile.TarInfo(name); m.mode = 0o600; m.size = len(data)
    return m, data


def write_tar(items):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=9, mtime=0) as z:
        with tarfile.open(fileobj=z, mode='w', format=tarfile.GNU_FORMAT) as t:
            for member, data in items:
                m = copy.copy(member); m.size = len(data); t.addfile(m, io.BytesIO(data))
    return buf.getvalue()


def once(raw, old, new):
    if raw.count(old) != 1: raise ValueError('patch context differs: '+repr(old[:80]))
    return raw.replace(old, new)


def bundle_of(raw):
    lines = [x for x in raw.decode().splitlines() if x.startswith('b=bytes.fromhex(')]
    if len(lines) != 1: raise ValueError('bundle inventory')
    return lines[0].encode(), bytes.fromhex(ast.literal_eval(ast.parse(lines[0]).body[0].value.args[0]))


def make_batch(raw, oldtoken, token, oldpub, pub, oldop, op):
    line, bundle = bundle_of(raw); parts = read_tar(bundle)
    if {m.name for m,d in parts} != {'0.py','0.json','7.py'}: raise ValueError('bundle differs')
    result = []
    for m, data in parts:
        if m.name == '0.json':
            assert data == oldpub; data = pub
        if m.name == '7.py':
            assert data == oldop; data = op
        result.append((m, data))
    raw = once(raw, line, ('b=bytes.fromhex(%r)' % write_tar(result).hex()).encode())
    return once(raw, oldtoken.encode(), token.encode())


def extract(raw, dest):
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=False)
    for m, data in read_tar(raw):
        p = dest/m.name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)


def build(destination=ROOT/'out', overlay=True, points=None, dense=False):
    if dense and (points or not overlay):raise ValueError('dense arm requires its own overlay package')
    if points and not overlay: raise ValueError('--points requires overlay')
    if points:
        api_pin = ROOT/'gpkg/point_runtime/PROMPT_API.json'
        if not api_pin.is_file() or json.loads(api_pin.read_text()).get('reviewed') is not True:
            raise ValueError('Point package blocked: SAM Prompt API source has not been reviewed within authorized read roots')
    parent = ROOT/'parent'; source = ROOT/'gpkg'
    names = ['0.json','0.tgz','3.py','BATCH.sh','CONFIG.json','INPUTS.example.json',
             'PACKAGE.json','SUBMIT.cmd','a/1.json','a/5.py','a/6.py','a/export.json']
    original = {n:(parent/n).read_bytes() for n in names}; nf = dict(original)
    pk = json.loads(nf['PACKAGE.json']); pub = json.loads(nf['0.json'])
    for n, h in pk['files'].items(): assert sha(nf[n]) == h, n
    assert sha(nf['0.tgz']) == pub['payload_sha256']
    entries = read_tar(nf['0.tgz']); pf = {m.name:d for m,d in entries}; before = dict(pf)
    plan = json.loads(pf['9.json']); oldtoken = plan['token']
    assert canonical(plan) == pub['plan_sha256']
    for n, pin in plan['payload_pins'].items():
        assert pin == dict(bytes=len(pf[n]), sha256=sha(pf[n])), n
    kit = ROOT/'kit2/kit/rerun2'
    for name in ('stage1','grounding'):
        assert pf['b/e2e_reader/'+name+'.py'] == (kit/('fixtures/'+name+'.py.txt')).read_bytes()
    if overlay:
        for path in sorted((source/'runtime').glob('*.py')): pf['g/'+path.name] = path.read_bytes()
        pf['g/0.json'] = (kit/'items544.json').read_bytes()
        pf['g/1.json'] = (kit/'ITEM_PINS.json').read_bytes()
        if points:
            raw = Path(points).read_bytes()
            value = json.loads(raw)
            import sys
            sys.path.insert(0,str(ROOT))
            from gpkg.runtime.q import validate
            validate(value['points'])
            if len(value['points']) != 150: raise ValueError('points require 150 items')
            pf['g/2.json'] = raw
            pf['g/3.json'] = jd(dict(points_sha256=sha(raw)))
            pf['g/4.json'] = api_pin.read_bytes()
            for path in sorted((source/'point_runtime').glob('*.py')):
                pf['g/'+path.name] = path.read_bytes()
            c = pf['g/c.py'].decode()
            c = once(c, "        s=o['selector']; n=len(o['candidates'])", '''        s=o['selector']; n=len(o['candidates'])
        if s.get('skipped') == 'point prompts':
            if s['invoked'] or s['slots'] is not None or n not in (0,1) or s['choice'] != (0 if n else -1):
                raise ValueError('invalid point selector skip')
            expected={} if not n else o['candidates'][0]['masks']
            if o['selected_masks'] != expected: raise ValueError('point selection differs')
            for mask in expected.values(): unrle(mask)
            continue''')
            pf['g/c.py'] = c.encode()

        if dense:
            from dense_build import overlay as dense_overlay
            dense_overlay(pf,source,once,jd)
        job = pf['orchard_h10/job.py'].decode()
        job = once(job, '\ndef main(root):', '\n'+(source/'upload.py').read_text()+'\n\ndef main(root):')
        insertion = '''        try:
            upload_capture(root,cfg,out,return_token,R)
        except Exception:
            pass  # Even a local receipt write failure cannot suppress the normal return.
        if not (out/'metadata/PARITY.json').exists():
            write(out/'metadata/PARITY.json',dict(trusted=False,items=0,expected=150,
                  failure='worker did not finish its receipt'))
'''
        job = once(job, '        if pool_ready:\n', insertion+'        if pool_ready:\n')
        pf['orchard_h10/job.py'] = job.encode()
        entry = pf['orchard_h10/entry.py'].decode()
        entry = once(entry, "else:raise ValueError('Invalid dispatch')", "elif action==3:\n    from g.w import run\n    result=run(cfg['config'],cfg['stop_at'])\n    raise SystemExit(1 if result and result['failure'] else 0)\nelse:raise ValueError('Invalid dispatch')")
        if points: entry = once(entry, 'from g.w import run', 'from g.pw import run')
        if dense: entry = once(entry, 'from g.w import run', 'from g.dw import run')
        pf['orchard_h10/entry.py'] = entry.encode()
        nf['a/6.py'] = (source/'dispatch.py').read_bytes()
        if dense:
            from dense_build import operator as dense_operator
            nf['a/6.py']=dense_operator(nf['a/6.py'],once)
        if points:
            operator = nf['a/6.py'].decode()
            operator = once(operator, "    cfg = prepare(config)[0]; root = control(cfg)", '''    cfg = prepare(config)[0]; root = control(cfg)
    from h1eval.h10.parity_adapter import settings_for, prepare_runtime
    from g.geometric import admit
    from g.points import load
    from g.w import load_rows
    runtime_settings = settings_for(cfg['settings'], 'devs1_routed')
    prepare_runtime(runtime_settings)
    admit(runtime_settings['sam3']['source_root'])
    here = Path(config['package'])/'g'
    load(here/'2.json', json.loads((here/'3.json').read_text())['points_sha256'], load_rows())''')
            nf['a/6.py'] = operator.encode()
        nf['a/9.py'] = (source/'cpu_receipt.py').read_bytes()
        nf['a/7.py'] = (source/'fetch_auth.py').read_bytes()
        guard = """import sys
if len(sys.argv)>1 and sys.argv[1] in ('check','submit'):
    for flag,value in (('--gpus','1'),('--time','05:00:00')):
        matches=[i for i,x in enumerate(sys.argv) if x==flag or x.startswith(flag+'=')]
        if not matches:sys.argv.extend([flag,value]);continue
        if len(matches)!=1:raise ValueError('duplicate '+flag)
        i=matches[0];got=sys.argv[i].split('=',1)[1] if '=' in sys.argv[i] else sys.argv[i+1]
        if got!=value:raise ValueError('requires '+flag+' '+value)
"""
        nf['3.py'] = once(nf['3.py'], b"with tarfile.open(p/'0.tgz') as t:", guard.encode()+b"with tarfile.open(p/'0.tgz') as t:")
        nf['SUBMIT.cmd'] = nf['SUBMIT.cmd'].replace(b'${A_N:?Set 1 to 4}',b'${A_N:-1}').replace(b'${A_T:?Set HH:MM:SS}',b'${A_T:-05:00:00}')
        seed = [(n, sha(pf[n])) for n in sorted(pf) if pf[n] != before.get(n)]
        seed += [(n,sha(nf[n])) for n in sorted(nf) if nf[n] != original.get(n)]
        token = 'a'+canonical(dict(parent=pub['payload_sha256'], changes=seed))[:12]
        plan['token'] = token
        for n in pf:
            if n != '9.json' and pf[n] != before.get(n):
                plan['payload_pins'][n] = dict(bytes=len(pf[n]),sha256=sha(pf[n]))
        pf['9.json'] = jd(plan)
        nf['0.tgz'] = write_tar([(m,pf[m.name]) for m,d in entries]+[added(n,pf[n]) for n in sorted(set(pf)-set(before))])
        assert sum(len(v) for v in pf.values()) < 32*1024**2
        pub.update(token=token,payload_bytes=len(nf['0.tgz']),payload_sha256=sha(nf['0.tgz']),plan_sha256=canonical(plan))
        nf['0.json'] = nf['CONFIG.json'] = jd(pub)
        nf['BATCH.sh'] = make_batch(nf['BATCH.sh'],oldtoken,token,original['0.json'],nf['0.json'],original['a/6.py'],nf['a/6.py'])
        pk['token'] = token; pk['files'] = {n:sha(nf[n]) for n in sorted(nf) if n != 'PACKAGE.json'}
        nf['PACKAGE.json'] = jd(pk)
    else:
        token = oldtoken
    delivery = write_tar([added(n,nf[n]) for n in sorted(nf)])
    changed = {n:dict(before=sha(before[n]) if n in before else None,after=sha(d))
               for n,d in pf.items() if before.get(n) != d}
    report = dict(token=token, package='/project/community/jjyeung/'+token,
                  job_name='a15_cot_ap'+token, walltime=WALLTIME,
                  delivery_bytes=len(delivery), delivery_sha256=sha(delivery),
                  installed_bytes=sum(len(d) for d in nf.values()), files={n:sha(d) for n,d in nf.items()},
                  payload_sha256=sha(nf['0.tgz']), plan_sha256=canonical(plan),
                  payload_files={n:sha(d) for n,d in pf.items()}, changed_payload=changed,
                  parent_token=oldtoken, no_overlay=not overlay)
    destination = Path(destination); destination.mkdir(parents=True,exist_ok=True)
    (destination/'delivery.tgz').write_bytes(delivery); (destination/'BUILD.json').write_bytes(jd(report))
    assert nf['a/1.json'] == original['a/1.json'] and nf['a/export.json'] == original['a/export.json']
    return report


def main():
    p = argparse.ArgumentParser(); p.add_argument('--out',type=Path); p.add_argument('--no-overlay',action='store_true')
    p.add_argument('--points',type=Path,nargs='?',const=Path('/scratch/jjyeung/orch_n30/nvkey1/work/c0/POINTS_gpt-6.2-astra.json'))
    p.add_argument('--dense',action='store_true')
    p.add_argument('--legacy-t1',action='store_true')
    a = p.parse_args()
    if a.legacy_t1:
        if a.points or a.dense or a.no_overlay:raise ValueError('legacy rebuild is separate')
        import sys
        sys.path.insert(0,str(ROOT))
        from dense_build import rebuild_legacy
        print(json.dumps(rebuild_legacy(a.out or ROOT/'out3/legacy_t1',ROOT)));return
    a.out = a.out or ROOT/('out3/dense' if a.dense else 'out_points' if a.points else 'out')
    r = build(a.out,overlay=not a.no_overlay,points=a.points,dense=a.dense)
    if a.dense:
        from scripts import render
        render(a.out,ROOT/'orchard_dense',cpu_partition='general')
    elif a.points:
        from scripts import render
        render(a.out,ROOT/'orchard_points',cpu_partition='general')
    elif not a.no_overlay and a.out.resolve() == (ROOT/'out').resolve():
        from scripts import render
        render()
    print(json.dumps({k:r[k] for k in ('token','delivery_bytes','delivery_sha256','plan_sha256','walltime')}))


if __name__ == '__main__': main()
