from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for label,old,doc,wall in [('b1','b1g','OPERATIONS_TOWER.md','05:00:00'),('b2','b2r','OPERATIONS_ROOM.md','02:30:00')]:
 d=W/label;token=(d/'TOKEN').read_text().strip();source=W.parent/old/'out';oldtoken=(source/'TOKEN').read_text().strip()
 oldtext=(source/doc).read_text();text=oldtext.replace(oldtoken,token).replace(sha(source/'1.tgz'),sha(d/'1.tgz'))
 # Preserve review requirements, resource guards, read semantics and scoring instructions.
 start=text.index('Coordinate staging IO')
 end=text.index('After the CPU check passes' if label=='b1' else 'Submit only after this command passes',start)
 cpu='''Coordinate staging IO before the allocated CPU check. This requests eight CPUs, 200G, four hours, no GPU, the preempt partition, and excludes orchard-flame-[0-31]. The helper creates a fresh private root, authenticates staging and restore, and runs the real 4 MiB return-pool write test through the process guard under its private `root/wpool`. It then sends the action-1 CPU rehearsal through the embedded bootstrap wrapper, which rewrites `a/5.py` to `7.py` and re-hashes the operator immediately before dispatch. The receipt must bind the write test, guard target, unchanged operator and dispatched argv, with `entry_sequence_passed=true` and `bundle_guard_passed=true`. A failed check must not proceed to GPU submission.

'''
 cpu+=('The CPU sequence checks selector wiring and the fixed G3T memory bound; it does not perform a real evaluation decode.\n\n' if label=='b1' else 'The CPU sequence also runs the first dev-S1 and R0-dev items through the full reader with the existing explicit model stubs. The receipt must contain both completed records. Stub scores do not measure model quality.\n\n')
 sbatch=f'''CPU_REPLY=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \\
  sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 \\
  --job-name=a15_cot_ap{token} --cpus-per-task=8 --mem=200G \\
  --time=04:00:00 --exclude='orchard-flame-[0-31]' --export=ALL --no-requeue \\
  --chdir=/tmp --output="$P/a/4.log" --error="$P/a/4.err" \\
  --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
CPU_JOB=${{CPU_REPLY%%;*}}
[[ "$CPU_JOB" =~ ^[0-9]+$ ]]
printf '%s\\n' "$CPU_JOB" > "$P/a/4.txt"'''
 cpu+='```bash\n'+sbatch+'\n```\n\nWait for the recorded CPU job to exit successfully. Then run this pass check (also saved as `sub2` and `commands_2.sh`); missing or mismatched evidence stops the workflow.\n\n'
 check='''/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['bundle_guard_passed'] is True and c['entry_sequence_passed'] is True
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
g=c['bundle_guard']
assert g['passed'] is True and g['path']=='7.py' and g['guard_target']=='6.py' and g['action']=='test'
assert g['operator_sha256']==sha(p/'a/6.py') and g['batch_sha256']==sha(p/'BATCH.sh')
e=c['entry_sequence'];root=Path(c['root'])
assert e['passed'] is True and e['entry_sequence_passed'] is True
assert e['events']==['guard_installed','write_test','operator_dispatch']
assert e['operator_sha256_before']==e['operator_sha256_after']==c['operator_sha256']
assert e['path']=='7.py' and e['guard_target']=='6.py' and e['action']=='test'
assert e['operator_sha256']==c['operator_sha256'] and e['batch_sha256']==sha(p/'BATCH.sh')
assert e['pool']==str(root/'wpool') and e['token']==v['token']
w=e['write_test']
assert type(w['bytes']) is int and w['bytes']==4*1024**2
assert isinstance(w['sha256'],str) and len(w['sha256'])==64 and all(ch in '0123456789abcdef' for ch in w['sha256'])
with tarfile.open(p/'0.tgz') as archive:
    guard_sha=hashlib.sha256(archive.extractfile('orchard_h10/vendor/return_io.py').read()).hexdigest()
assert e['guard_target_sha256']==guard_sha
assert {k:v for k,v in e.items() if k!='entry_sequence_passed'}==g
assert e['requested_argv'][-2:]==[str(root/'a/5.py'),str(root/'a/1.json')]
assert e['dispatched_argv']==e['requested_argv'][:-2]+[str(root/'7.py'),str(root/'a/1.json')]
m=c['memory']
assert m==json.loads((p/'a/c/MEMORY.json').read_text())
assert m['fits'] is True and m['basis']=='fixed_g3t_shapes'
assert m['perception_memo_modules']==['g3t'] and m['sam_measurement_required'] is False
'''
 if label=='b2':
  check+='''assert c['full_reader_passed'] is True
import runpy
runpy.run_path(str(p/'a/5.py'))['validate_full_reader']([{'full_reader':c['full_reader']}])
rows=c['full_reader']['records']
assert [(r['set'],r['item']) for r in rows]==[('dev-S1','room_scene0155_00'),('R0-dev','r0_015bd4aaf6870d79bade')]
assert c['full_reader']==json.loads((p/'a/c/FULL_READER.json').read_text())
'''
 check+="print('All CPU receipt checks passed')\nPYCODE"
 cpu+='```bash\n'+check+'\n```\n\n'
 text=text[:start]+cpu+text[end:]
 text=text.replace("into W5's `work/f/`",f"into `{d}/work/f/`").replace("into W6's `work/f/`",f"into `{d}/work/f/`")
 text=text.replace(f'cd /scratch/jjyeung/orch_n30/reader_r1/work/{old}',f'cd {d}')
 for name in ('unpack_return.py','tower_pair.py','room_pair.py'):
  text=text.replace('out/'+name,name)
 text=text.replace('--package out/src','--package src').replace('--out out/tower_results','--out work/scores').replace('--out out/scores','--out work/scores')
 text=text.replace('../b1p/in/h10own/', '/scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/h10own/')
 text=text.replace("The allocation matches W5", "The CPU allocation uses the specified resources")
 text=text.replace("original pool and GCS transport remain pinned to W5", "pool and GCS transport retain their sealed pins")
 text=text.replace('These commands have not run in this lane.','These commands require the operator to run them on Orchard.').replace('These are operator commands; this lane ran none of them.','These commands require the operator to run them on Orchard.')
 text+='\nThe sealed delivery is `1.tgz`; its receipt is `PACKAGE.json`. `READ_PLAN.json` records the read settings and commands. `FILE_SHA256_DIFF.tsv` lists every changed sealed member and build source against the source package. Local fixture receipts do not authorize Orchard submission. No Orchard CPU check, network transfer, or GPU job ran during this repair.\n'
 (d/doc).write_text(text)
 blocks=[];inside=False
 for line in text.splitlines():
  if line=='```bash':inside=True;blocks.append([])
  elif line=='```':inside=False
  elif inside:blocks[-1].append(line)
 # Keep command blocks independently reviewable: CPU submission is asynchronous.
 commands={name:'\n'.join(block) for name,block in zip(['placement_and_metadata','cpu_sbatch','cpu_pass_check','submit','fetch','unpack_and_score'],blocks)}
 assert len(blocks)==6
 plan=json.loads((d/'READ_PLAN.json').read_text());plan['commands']=commands;plan['operations_file']=doc
 (d/'READ_PLAN.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
 (d/'sub2').write_text('#!/usr/bin/env bash\nset -euo pipefail\n'+check+'\n')
 (d/'COMMANDS.json').write_text(json.dumps(commands,indent=2)+'\n')
 for i,block in enumerate(blocks):
  (d/f'commands_{i}.sh').write_text('\n'.join(block)+'\n')
