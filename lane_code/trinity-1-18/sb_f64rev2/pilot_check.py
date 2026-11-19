"""CPU-only pilot preflight and an explicit failed-row fixture; never loads weights or CUDA."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent; KIT=ROOT.parent/'sb_f64fix/kit'
sys.path[:0]=[str(KIT/'scripts'),os.environ['F64_TREE']]
import token_audit as T
import mem_pilot as P
inputs={}
def sha(p):
    p=Path(p); inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest(); return inputs[str(p)]
for p in [Path(__file__),ROOT/'run_cpu.sh',KIT/'scripts/token_audit.py',KIT/'scripts/mem_pilot.py',KIT/'configs/r1_config_f64.json']:
    sha(p)
config=KIT/'configs/r1_config_f64.json'
commands=[]
for argv in [[str(KIT/'scripts/token_audit.py'),'run','--config',str(config),'--out',str(ROOT/'tmp/unbound_shard.jsonl')], [str(KIT/'scripts/mem_pilot.py'),'--config',str(config),'--audit',str(ROOT/'tmp/MISSING_summary.json'),'--out',str(ROOT/'tmp/unbound_pilot')]]:
    result=subprocess.run([sys.executable,'-B',*argv],cwd=ROOT,capture_output=True,text=True)
    commands.append(dict(argv=[sys.executable,'-B',*argv],returncode=result.returncode,stderr=result.stderr,stdout=result.stdout))
# Change one audited fixture row to an honest check_row failure, preserving all identity and coverage fields.
shards=sorted((ROOT/'tmp/dryrun').glob('token_audit_*/complete_*.jsonl'))
assert len(shards)==2
outdir=ROOT/'tmp/pilot_failed_row';outdir.mkdir(exist_ok=False)
newpaths=[];failed_key=None
for p in shards:
    sha(p); lines=[json.loads(x) for x in p.read_text().splitlines()]; header=lines[0]; rows=lines[1:-1]
    if failed_key is None:
        rec=next((r for r in rows if r['stream']=='routing'),None)
        if rec:
            failed_key=(rec['stream'],rec['index']);rec['check_row']='ValueError: injected stale-frame failure (review fixture)'
    items=[((r['stream'],r['index']),(r['first_step'],r['rank'])) for r in rows]
    target=outdir/p.name
    T.write_shard(target,header['identity'],header['shard']['index'],items,lambda part,sink:[sink(r) for r in rows])
    newpaths.append(target)
summary=T.summarize([str(p) for p in newpaths],T.file_sha256(config))
summary_path=outdir/'SUMMARY.json';summary_path.write_text(json.dumps(summary))
try:
    accepted=P.check_audit(summary_path,config)
    control=dict(pilot_accepted=True,launch_ready=accepted['launch_ready'],errors=accepted['errors'],flagged=accepted['flagged'],failed_key=failed_key,failed_row_in_longest=any((stream,r['index'])==failed_key for stream,rs in accepted['longest'].items() for r in rs))
except Exception as e: control=dict(pilot_accepted=False,reason=str(e))
for rel in ['student_pilot/carrier_c1_run.py','student_pilot/carrier_c1.py','student_pilot/full_ft.py','student_pilot/r1_training.py','launch_r1/entry.py']:
    sha(Path(os.environ['F64_TREE'])/rel)
value=dict(command='bash run_cpu.sh pilot_check.py',scope='CPU preflight plus explicitly injected failure in synthetic audited fixtures; no GPU measurement or production plan.',input_sha256=inputs,unbound_commands=commands,failed_row_control=control,static_assessment=dict(fsdp='wrap_model -> FULL_SHARD, use_orig_params, BF16 compute, FP32 reduce',masters='prepare_model casts base to FP32; pilot checks trainable base dtypes; wrap_full_model checks every base parameter',adam='trainer parameter_groups and AdamW; optimize_step performs optimizer.step; pilot records state bytes',checkpointing='carrier_c1.py enables use_reentrant=False; pilot checks enabled and writes rank-sharded checkpoint',accumulation='same first-step stream schedule; len(plan)*world == global_batch; substitutes longest rows per stream',gap='check_audit permits check_row failures and excludes failed rows from longest; reject non-tripwire failures before a pilot'))
(ROOT/'out/pilot_review.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(dict(unbound=[dict(returncode=c['returncode'],last_error=c['stderr'].splitlines()[-1]) for c in commands],failed_row_control=control),indent=2))
