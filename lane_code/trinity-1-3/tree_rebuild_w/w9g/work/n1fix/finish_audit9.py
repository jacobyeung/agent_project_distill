"""Verify final source, mix bytes and input pins without changing the tree."""
import base64,hashlib,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,load,pinned,sha256
seal=json.loads((L/'out/TREE_SEAL.json').read_text())
assert digest(inventory(T))==seal['tree_sha256']
bindings={}
for arm in ('a0','a2','r1'):
    root=B/'kits'/arm;evidence=load(root/'k/8.json')
    if arm=='r1':
        cfg=load(root/'k/c.json');pin=cfg['r1_training']['mix']
        raw=base64.b64decode(load(root/'k/s.json')['entries'][pin['path']]['payload'],validate=True)
        report='out/MIX_R1.json'
    else:
        pin=evidence['mix'];raw=(root/pin['path']).read_bytes()
        report='out/MIX_A0.json' if arm=='a0' else 'out/MIX_A2.json'
    assert raw==(L/report).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==pin['sha256']==evidence['report_sha256']
    assert (L/evidence['report_file']).read_bytes()==raw
    bindings[arm]=dict(report=report,cited_report=evidence['report_file'],sha256=pin['sha256'],byte_equal=True)
(B/'MIX_BINDINGS.json').write_text(json.dumps(bindings,indent=2)+'\n')
pin=load(B/'inputs/config.json')['remove_files'][-1]
assert pinned(pin)
assert pin['sha256']=='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411'
result=dict(source_seal=seal['tree_sha256'],mixes=bindings,removal_pin=pin,GO=False)
(B/'FINAL_BINDING_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
