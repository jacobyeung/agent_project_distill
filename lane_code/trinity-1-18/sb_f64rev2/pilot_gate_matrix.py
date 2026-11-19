"""Distinguish permitted calibration rows from row failures using retained synthetic audit records."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;KIT=ROOT.parent/'sb_f64fix/kit';CFG=KIT/'configs/r1_config_f64.json'
sys.path[:0]=[str(KIT/'scripts'),os.environ['F64_TREE']]
import token_audit as T
import mem_pilot as P
paths=sorted((ROOT/'tmp/dryrun').glob('token_audit_*/complete_*.jsonl'));assert len(paths)==2
source={str(p):T.file_sha256(p) for p in [Path(__file__),ROOT/'run_cpu.sh',CFG,KIT/'scripts/token_audit.py',KIT/'scripts/mem_pilot.py',*paths]}
records={p:[json.loads(x) for x in p.read_text().splitlines()] for p in paths}
values={}
for case in ['passing','tripwire_only','failed_check']:
    folder=ROOT/'tmp'/('pilot_matrix_'+case);folder.mkdir(exist_ok=False);generated=[]
    for p,lines in records.items():
        identity=json.loads(json.dumps(lines[0]['identity']));rows=[dict(r) for r in lines[1:-1]]
        if case=='tripwire_only':
            identity['limits']['tripwire_tokens']=9200
            for r in rows:r['over_tripwire']=r['tokens']>9200
        if case=='failed_check':
            for r in rows:
                if r['stream']=='routing' and r['index']==0:r['check_row']='ValueError: injected invalid row (synthetic control)'
        items=[((r['stream'],r['index']),(r['first_step'],r['rank'])) for r in rows]
        q=folder/p.name;T.write_shard(q,identity,lines[0]['shard']['index'],items,lambda part,sink:[sink(r) for r in rows]);generated.append(str(q))
    summary=T.summarize(generated,T.file_sha256(CFG));q=folder/'summary.json';q.write_text(json.dumps(summary))
    try:P.check_audit(q,CFG);accepted=True;error=None
    except ValueError as e:accepted=False;error=str(e)
    values[case]=dict(pilot_accepted=accepted,launch_ready=summary['launch_ready'],errors=summary['errors'],failed_rows=sum(v['failed'] for v in summary['streams'].values()),tripwire_rows=sum(v['over_tripwire'] for v in summary['streams'].values()),longest_row_count=sum(len(v) for v in summary['longest'].values()),required_behavior='accept' if case!='failed_check' else 'refuse',error=error)
value=dict(command='bash run_cpu.sh pilot_gate_matrix.py',scope='Explicit synthetic controls from the retained real encode fixtures; no production admission or GPU execution.',input_sha256=source,cases=values)
(ROOT/'out/pilot_gate_matrix.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(values,indent=2))
