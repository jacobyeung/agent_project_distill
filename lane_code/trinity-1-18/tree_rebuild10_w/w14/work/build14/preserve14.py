from pathlib import Path
import json,hashlib,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build14';T=L/'work/tree_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=B/'BASE13_SEAL.json'
if not old.exists():old.write_bytes((L/'out/TREE_SEAL.json').read_bytes())
base=json.loads(old.read_text());assert base['tree_sha256']=='35d4b18b033da1be95c6453469330537578155abd17ecb10e850765729f187ad'
changed=[name for name,h in base['files'].items() if sha(T/name)!=h]
stable=['student_pilot/'+n+'.py' for n in ['carrier_c1_run','r1_population','r1_routing','r1_mix','r1_loader','row_text_audit','r2_intake','r2_adapters','depth_readout','r2_openers'] if (T/'student_pilot'/ (n+'.py')).exists()]
assert all(sha(T/name)==base['files'][name] for name in stable)
cfg=json.loads((B/'inputs/kit_config.json').read_text())
assert cfg['init_artifact']['artifact']['sha256']=='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
value={'base13_seal':base['tree_sha256'],'changed_existing_files':changed,'unchanged_contracts':{n:sha(T/n) for n in stable},
    'step544_parent':cfg['init_artifact']['artifact'],
    'parity':{'result':'work/build12/proofs/depth_sweep/RESULT.json','result_sha256':sha(L/'work/build12/proofs/depth_sweep/RESULT.json'),
        'rerun':False,'reason':'The package omits geo_dump.py and b11_legacy.json, and their external paths are not authorized by this build. Unchanged implementation and authenticated prior result only.'},
    'behaviors':['handover default deny','receipt closure and forged preparation/completion refusal','Unicode authored-think rules','M1 fixed-buffer binding','L1 typed refusals',
        'F1-F6 original counts 1532/0/0, 2000/1186/1102, 2000/1222/1119, 476/0/431','repaired counts 777/1476/8067','601-key exclusion','144000/144000 parity evidence',
        'population source membership and native reader offsets','routing base replacement','1000-step plan and maximum repeat 4','GO=false kits and host-only production audit'],
    'source_report':'out/BUILD13_REPORT.md','source_report_sha256':sha(L/'out/BUILD13_REPORT.md')}
(B/'PRESERVATION.json').write_text(json.dumps(value,indent=2))
print(json.dumps({'changed':changed,'stable':len(stable)}))
