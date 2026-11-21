"""Prepare local upload streams from an independent task-A verdict."""
from pathlib import Path
import base64, gzip, hashlib, importlib.util, json, os, re, resource, shutil, subprocess, sys, tempfile, time
resource.setrlimit(resource.RLIMIT_AS, (14*1024**3, 14*1024**3))
L=Path(__file__).resolve().parents[1]
D=L/'work/build24m4z11'
E=L.parent/'work/d173912/173912'
SELECTION='a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73'
GENERATED='5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df'
DIGEST='522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39'
RECEIPT='38c52f008d131a8554d3d18974f4d2de1e77bdf092c747132df477db8ff08398'
METADATA='3ee233af526a4f82be382591bb78727c0262dfccdf5fcd26a3563ed3ff8e8461'
BASE='ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984'
SOURCE_SEALS={'q':'df93cfba9769ca82f48ac3bfdbb117ffc2d06b6f694ed1694c23d815fa97e2a9',
 'n':'fb5c7f62c91b55cf0b432e65fd79d582c581b1fa27aa5b23ef36bb8001fab867',
 'n_go':'5c8ba4b4dc52c08388b4e911dd77ea3a380a79a53eb6389010ff9fb666fe2b4d'}
sys.path[:0]=[str(L/'out'),str(L/'work/tree_r1c')]
import arm_routing as arm
# Keep all executable dependencies in this delivered workspace.
sys.path[:]=[p for p in sys.path if not p.startswith(str(L.parent)+'/') or p.startswith(str(L)+'/')]
sys.path.insert(0,str(L/'work/tree_r1c'))
J=arm.J

def write(p,v):
    p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')

def inventory(root):
    result={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise ValueError('R1_ARM_SYMLINK:'+str(p))
        if p.is_file():result[str(p.relative_to(root))]=dict(sha256=J.sha(p),mode=p.stat().st_mode&511,bytes=p.stat().st_size)
    return result

def verify(root,expected):
    if J.seal(root)!=expected or J.load(root/'BUILD.json')['kit_sha256']!=expected:
        raise ValueError('R1_ORIGIN_SEAL_DIFFERS:'+str(root))

def reviewed(verdict):
    if not verdict.is_file():raise ValueError('R1_REVIEW_VERDICT_MISSING:'+str(verdict))
    # Select the expected identities from the actual verdict; the helper still
    # performs its complete independent verdict and receipt checks.
    hashes={h.lower():h.lower() for h in re.findall(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])',verdict.read_text())}
    if SELECTION not in hashes:raise ValueError('R1_REVIEWED_SELECTION_DIFFERS')
    if GENERATED not in hashes:raise ValueError('R1_REVIEWED_REGENERATED_DIFFERS')
    return hashes[SELECTION],hashes[GENERATED]

def prepare(verdict,seconds,*,evidence=E,parent=L):
    start=time.monotonic();verdict=Path(verdict).resolve()
    selected,generated=reviewed(verdict)
    # Match set_stop.py's syntax and range before creating copies.
    if not isinstance(seconds,str) or not seconds.isascii() or not seconds.isdigit():raise ValueError('expected one integer')
    stop=int(seconds)
    if not 3600<=stop<=10800 or stop%300:raise ValueError('expected multiple of 300 in [3600,10800]')
    evidence=Path(evidence);parent=Path(parent).resolve()
    if not parent.is_relative_to(L):raise ValueError('R1_ARM_OUTPUT_OUTSIDE_WORKSPACE')
    for name,h,code in [('routing_selection.json',SELECTION,'R1_REVIEWED_SELECTION_DIFFERS'),('receipt.json',RECEIPT,'R1_RECEIPT_BYTES_DIFFERS'),('db_bytes.json',METADATA,'R1_DB_BYTES_DIFFERS')]:
        if J.sha(evidence/name)!=h:raise ValueError(code)
    origins={'q':L/'work/build24/kits/q','n':L/'out/kit_n','n_go':L/'out/kit_n_go'}
    before={}
    for n,p in origins.items():verify(p,SOURCE_SEALS[n]);before[n]=inventory(p)
    overlay=json.loads((D/'OVERLAY_FILES.json').read_text());overlay_seals=json.loads((D/'OVERLAY_SEALS.json').read_text())
    if overlay_seals['q']!=SOURCE_SEALS['q'] or overlay_seals['n']!='797255ae1421d27f6c65bb9fc0038da1f345f446e1e1d41c90ba1bdf8f2338f7':raise ValueError('R1_OVERLAY_DIFFERS')
    run=Path(tempfile.mkdtemp(prefix='a_',dir=parent));copies=run/'sources';copies.mkdir()
    for n,p in origins.items():shutil.copytree(p,copies/('kit_'+n))
    shutil.copyfile(L/'out/set_stop.py',copies/'set_stop.py')
    if stop!=3600:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(copies/'set_stop.py'),seconds],capture_output=True,text=True)
        (run/'SET_STOP.log').write_text(result.stdout+result.stderr)
        if result.returncode:raise ValueError('R1_SET_STOP_FAILED:'+result.stdout+result.stderr)
    layout=dict(origins={n:str(copies/('kit_'+n)) for n in origins},baseline_files=str(D/'OVERLAY_FILES.json'),baseline_seals=str(D/'OVERLAY_SEALS.json'),baseline_label='Current reviewed Orchard q/n overlay (24m4y2)')
    write(run/'layout.json',layout)
    result=arm.apply(evidence/'routing_selection.json',evidence/'db_bytes.json',run/'armed',
        reviewed_selection_sha256=selected,reviewed_regenerated_sha256=generated,review_verdict=verdict,
        regenerated_receipt_path=evidence/'receipt.json',base_path=L/'work/build24m4m/inputs'/BASE,kit_layout=run/'layout.json')
    kits=run/'armed/kits'
    # Preserve the exact authenticated GO capsule of the final n_go template.
    ng=kits/'n_go';shutil.copyfile(copies/'kit_n_go/k/a.json',ng/'k/a.json')
    build=J.load(ng/'BUILD.json');build['GO']=J.load(copies/'kit_n_go/BUILD.json')['GO'];arm.cap(ng/'BUILD.json',build)
    seals={n:arm.reseal(kits/n) for n in origins}
    for n in origins:
        scan=arm.scan(kits/n,n)
        (run/('SCAN_'+n+'.json.gz')).write_bytes(gzip.compress(json.dumps(scan,sort_keys=True).encode(),mtime=0))
        verify(kits/n,seals[n])
        assert J.load(kits/n/'k/a.json')['GO']==(n=='n_go')
        assert J.load(kits/n/'BUILD.json')['GO']==J.load(origins[n]/'BUILD.json')['GO']
    changes={};after={n:inventory(kits/n) for n in origins}
    for n in origins:
        assert set(before[n])==set(after[n]),('R1_ARM_FILE_SET_DIFFERS',n)
        changes[n]=[r for r in before[n] if before[n][r]!=after[n][r]]
        allowed={'k/h.json','k/r.json','k/p.json','k/a.json','BUILD.json','SHA256SUMS.txt'}
        if n!='q' and stop!=3600:allowed.add('k/n.json')
        assert set(changes[n])<=allowed,('R1_ARM_UNEXPECTED_CHANGE',n,changes[n])
        assert inventory(origins[n])==before[n],('R1_ORIGIN_CHANGED',n)
    # The public streams compare against the current overlay, not helper defaults.
    def manifest(names,stem):
        rows=[]
        for n in names:
            if set(overlay[n])-set(after[n]):raise ValueError('R1_OVERLAY_REMOVAL_REQUIRED:'+n)
            for rel,v in after[n].items():
                old=overlay[n].get(rel)
                if old and (old['sha256'],old['mode'])==(v['sha256'],v['mode']):continue
                rows.append(dict(name=n+'/'+rel,local_path=str(kits/n/rel),bytes=v['bytes'],sha256=v['sha256'],mode=format(v['mode'],'04o'),action='replace' if old else 'add',baseline_sha256=old['sha256'] if old else None))
        if names==['q','n']:
            p=run/'armed/upload/u'/selected
            rows.append(dict(name='u/'+selected,local_path=str(p),bytes=p.stat().st_size,sha256=selected,mode='0644',action='add_or_verify'))
        # Upload payloads first, the per-kit seals last. No live launch occurs here.
        rows.sort(key=lambda r:(2 if r['name'].endswith('/BUILD.json') else 1 if r['name'].endswith('/SHA256SUMS.txt') else 0,r['name']))
        value=dict(schema='armed-upload-v1',baseline='Current reviewed Orchard overlay',baseline_kit_seals={n:overlay_seals[n] for n in names},kits={n:seals[n] for n in names},files=rows,total_files=len(rows),total_bytes=sum(r['bytes'] for r in rows),GO=names==['n_go'],uploaded=False,launched=False,review_verdict=dict(path=str(verdict),sha256=J.sha(verdict)),stop_before_seconds=stop,already_staged=result['already_staged'],requires_ordinary_stream=names==['n_go'])
        write(run/(stem+'.json'),value);(run/(stem+'.list')).write_text(''.join(r['name']+'\n' for r in rows))
        return value
    ordinary=manifest(['q','n'],'UPLOADS_ARMED');go=manifest(['n_go'],'UPLOADS_ARMED_GO')
    assert all(not r['name'].startswith('n_go/') for r in ordinary['files'])
    envelope=json.loads((ng/'k/c.json').read_bytes());payload=base64.b64decode(envelope['payload'],validate=True)
    payload_hash=hashlib.sha256(payload).hexdigest();assert payload_hash==envelope['sha256']
    summary=dict(status='OK',output=str(run),kits=seals,armed_n_go_config=dict(payload_sha256=payload_hash,file_sha256=J.sha(ng/'k/c.json')),changes=changes,seconds=round(time.monotonic()-start,3),stop_before_seconds=stop,ordinary_files=ordinary['total_files'],go_files=go['total_files'],uploaded=False,launched=False)
    write(run/'SUMMARY.json',summary)
    return summary

def main():
    if len(sys.argv)!=3:raise ValueError('Usage: arm_launch.sh REVIEW_VERDICT_FILE STOP_BEFORE_SECONDS')
    print(json.dumps(prepare(sys.argv[1],sys.argv[2]),sort_keys=True))
if __name__=='__main__':main()
