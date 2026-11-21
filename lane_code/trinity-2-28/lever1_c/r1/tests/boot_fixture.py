"""Small local inputs at the production job.stage boundary; no bulk sources."""
import io
import json
from pathlib import Path
import sys
import tarfile
import time


def configure(job,root,package,cfg,inputs,S,J,case):
    import hashlib
    from unittest.mock import patch
    original_stage=job.stage
    original_copy=S.copy_parts
    actual_physical=J.physical
    logical=str(actual_physical(root,cfg['logical']))
    localcfg=dict(cfg,logical=logical)
    d=Path(logical)/'d';d.mkdir(parents=True,exist_ok=True)
    policy=b'#!/bin/bash\nexec "$@"\n'
    envtar=root/'31'
    with tarfile.open(envtar,'w') as archive:
        for name,data in [('q/0',policy),('q/1',b'pass\n'),('v/0',b'local environment binding')]:
            item=tarfile.TarInfo(name);item.size=len(data);archive.addfile(item,io.BytesIO(data))
    empty=root/'32'
    with tarfile.open(empty,'w'):pass
    def pin(path):return dict(path=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    def spec(path):return dict(parts=[pin(path)],sha256=pin(path)['sha256'],destination=str(d.relative_to(root)),expanded_bytes=10240)
    # Archive 3 provides this fixture's environment and policy files.
    ins=dict(inputs,python=sys.executable,archives=[spec(empty),spec(empty),spec(empty),spec(envtar),spec(empty)],
             policy=dict(vnice=str(d/'q/0'),terminator=str(d/'q/1')))
    assets=dict(groups=[],bwrap_pin=pin(empty),vnice_sha256=hashlib.sha256(policy).hexdigest(),terminator_sha256=hashlib.sha256(b'pass\n').hexdigest())
    asset_text=(Path(job.__file__).parent/'vendor/ORCHARD_ASSETS.json').read_text()
    real_loads=json.loads
    def loads(raw,*args,**kwargs):return assets if raw==asset_text else real_loads(raw,*args,**kwargs)
    counts=dict(bulk_bytes=0,bulk_calls=0)
    def copy(parts,dest,opener,**kwargs):
        if dest.name=='c':return original_copy(parts,dest,lambda p:(package/'0.tgz').open('rb'),**kwargs)
        if dest.name.startswith('a'):
            counts['boot_passed_before_bulk']=json.loads((Path(logical)/'r/metadata/25.json').read_text())['passed']
            counts['bulk_calls']+=1;counts['bulk_bytes']+=sum(p['bytes'] for p in parts)
            raise AssertionError('bulk source opened before failed boot')
        return original_copy(parts,dest,opener,**kwargs)
    # Inject a missing deferred dependency into the authenticated local fixture.
    # Production bytes stay unchanged; the actual numeric worker discovers it.
    real_extract=S.extract_stream
    def extract(stream,destination,*args,**kwargs):
        result=real_extract(stream,destination,*args,**kwargs)
        if str(destination).endswith('/p'):
            import j
            path=Path(destination)/'g/3.json';manifest=json.loads(path.read_text())
            if case=='boot_success':manifest=dict(modules=['keyword','xml.sax.expatreader','g.w'],symbols=[])
            else:manifest['modules'].insert(0,'a_missing_closure')
            raw=j.pack(j.wire_dumps(manifest));path.write_bytes(raw)
            localcfg['payload_pins']=dict(cfg['payload_pins'])
            localcfg['payload_pins']['g/3.json']=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        return result
    started=time.monotonic()
    try:
        with patch.object(job.json,'loads',side_effect=loads),patch.object(S,'copy_parts',side_effect=copy),\
             patch.object(S,'extract_stream',side_effect=extract),patch.object(S,'room'),\
             patch.object(J,'physical',side_effect=lambda r,p:Path(p)),patch.object(J,'namespace',return_value=[]):
            original_stage(root,localcfg,ins,S,J)
    finally:
        counts['seconds']=time.monotonic()-started
        (root/'33.json').write_text(json.dumps(counts))
