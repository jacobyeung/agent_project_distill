#!/bin/bash
set -euo pipefail
export TZ=UTC
umask 077
O=/project/community/jjyeung/okh7
private_dir() {
    [[ -d "$1" && ! -L "$1" && "$(stat -c %a -- "$1")" == 700 ]] || {
        printf 'Directory must be mode 0700; run: chmod 700 -- %q\n' "$1" >&2
        exit 3
    }
}
private_dir "$O"
BUN=/project/community/jjyeung/okh7/i_d6da12b8
KH=/project/community/jjyeung/okh7/x_d6da12b8
private_dir "$BUN"
private_dir "$KH"
cd "$BUN"
sha256sum -c sums.txt
# The separate approval record is supplied by the operator, never inferred from 4.json.
env -u PYTHONOPTIMIZE python3 -I -B - "$KH" "$BUN" <<'P'
import hashlib,json,sys,os,re
from pathlib import Path
k,b=map(Path,sys.argv[1:]);go=json.loads((b/'go.json').read_text());ids=json.loads((b/'ids.json').read_text())
assert go.get('production_go_granted') is True and go.get('config_sha256')==ids['identity'] and go.get('admission_contract_sha256')==ids['contract'] and go.get('wrapper_sha256')==hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest()
assert go.get('manifest_sha256')==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
job=os.environ.get('PROOF_JOB','')
if go.get('canary') is True:
 import subprocess
 assert os.environ.get('ADMISSION_JOB')=='170956', 'ADMISSION_JOB must be 170956'
 assert re.fullmatch('[1-9][0-9]*',job) and job!='170956', 'Invalid parallel PROOF_JOB'
 assert (b/'job.id').read_text().strip()==job, 'PROOF_JOB differs from bundle job.id'
 old=Path('/project/community/jjyeung/okh7/x_69d2930d.f170956')
 def pinned(path, expected):
  assert not path.is_symlink(), 'Linked evidence: '+str(path)
  raw=path.read_bytes()
  assert hashlib.sha256(raw).hexdigest()==expected, 'Evidence SHA differs: '+str(path)
  return raw
 receipt=json.loads(pinned(old/'o/170956.proof.json', '164ef356f5bb88953d8e776a41cc5aead611cf4202283c63c4bcaae7c93f2b70'))
 log=pinned(old/'o/170956.proof.log', '911729ca1b9c0477bd64e5148f15db896b7ddf083fb7e6850f63c5ce5211c804').decode()
 assert receipt.get('job')=='170956'
 assert receipt.get('config_identity')==ids['identity'] and receipt.get('contract_sha256')==ids['contract'], 'Admission identity/contract differs'
 exits=re.findall(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ \| exit rc=(\d+)$',log,re.M)
 assert exits==['0'], 'Admission did not end exit rc=0'
 # The receipt authenticates the old config and the entire old kit manifest.
 # These carry the store and routing pins that the human log does not print.
 manifest=pinned(old/'SHA256SUMS.txt',receipt['manifest_sha256']).decode()
 old_sums={}
 for line in manifest.splitlines():
  digest,name=line.split('  ',1)
  assert name not in old_sums and not Path(name).is_absolute() and '..' not in Path(name).parts
  assert re.fullmatch('[0-9a-f]{64}',digest)
  old_sums[name]=digest
 def old_json(name):
  return json.loads(pinned(old/name,old_sums[name]))
 old_cfg_pin=receipt['config']
 assert old_sums[old_cfg_pin['file']]==old_cfg_pin['sha256']
 old_cfg=old_json(old_cfg_pin['file'])
 launch=json.loads((k/'k/launch.json').read_text())
 cfg=json.loads(pinned(k/launch['config']['file'],launch['config']['sha256']))
 for field in ('streams','s1_routing','remove_files','type_mix'):
  assert old_cfg[field]==cfg[field], 'Staged config differs: '+field
 current=json.loads((k/'k/0.json').read_text())
 assert old_json('k/0.json')==current, 'Staged input hashes differ'
 assert hashlib.sha256((k/'b/c.sh').read_bytes()).hexdigest()==receipt['runtime_sha256']['b/c.sh']==old_sums['b/c.sh'], 'Staging implementation differs'
 assert receipt['selection']==cfg['s1_routing']['selection'], 'Selection differs'
 store=json.loads((b/'d.json').read_text())
 assert hashlib.sha256((b/'d.json').read_bytes()).hexdigest()==cfg['streams']['vqa']['sha256']
 extras={e['dest']:e['sha256'] for e in current['extra']}
 assert extras[store['database']['path']]==store['database']['sha256'], 'Store differs'
 unit=cfg['type_mix']['unit_rows']
 assert extras[unit['path']]==unit['sha256'], 'Unit slice differs'
 removals={}
 for line in log.splitlines():
  if line.startswith('{'):
   row=json.loads(line)
   if 'remove_list' in row:
    pin=row['remove_list']['file'];path=pin['path'];digest=pin['sha256']
    assert path not in removals or removals[path]==digest, 'Conflicting REMOVE log entries'
    removals[path]=digest
 assert removals=={p['path']:p['sha256'] for p in cfg['remove_files']}, 'REMOVE hashes differ'
 state=subprocess.run(['squeue','--noheader','--jobs',job,'--format=%i|%T|%j'],
  env=dict(os.environ,TZ='UTC'),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=30)
 rows=[line.strip().split('|') for line in state.stdout.splitlines() if line.strip()]
 assert len(rows)==1 and rows[0][0]==job and rows[0][1] in ('PENDING','RUNNING') and rows[0][2]=='a15_cot_ap673bc60f', 'Parallel proof is not active under the pinned name'
 assert ids['job_name']=='a15_cot_ap673bc60f'
else:
 assert re.fullmatch('[1-9][0-9]*',job), 'PROOF_JOB must identify the completed CPU proof'
 proof=json.loads((k/'o'/(job+'.proof.json')).read_text())
 launch=json.loads((k/'k/launch.json').read_text())
 assert proof.get('status')=='PASS' and proof.get('rc')==0 and proof.get('job')==job
 assert proof.get('config_identity')==ids['identity'] and proof.get('contract_sha256')==ids['contract']
 assert proof.get('config')==launch['config'] and proof.get('manifest_sha256')==go['manifest_sha256']
 assert proof.get('wrapper_sha256')==go['wrapper_sha256'] and proof.get('cuda_visible_devices')==''
 assert proof.get('effective_config_verified') is True and proof.get('first_batch_executed') is False
 assert proof.get('training_executed') is False and proof.get('admission_result', dict()).get('status')=='PREPARED'
 assert proof.get('prepared_seals') and proof.get('real_job_reuse') is False
 for name in ('disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','directory_modes','loader_audit','required_families'):
  assert proof.get('checks',{}).get(name,{}).get('status')=='PASS', name

sys.path.insert(0,str(k/'b'));import a;a.main(k)
if go.get('canary') is True:
 record=dict(canary=True,admission_job='170956',proof_job=job,config_identity=ids['identity'],
  contract_sha256=ids['contract'],manifest_sha256=go['manifest_sha256'],wrapper_sha256=go['wrapper_sha256'],
  admission_receipt_sha256='164ef356f5bb88953d8e776a41cc5aead611cf4202283c63c4bcaae7c93f2b70',admission_log_sha256='911729ca1b9c0477bd64e5148f15db896b7ddf083fb7e6850f63c5ce5211c804',
  proof_state=rows[0][1],job_name=ids['job_name'],submission='GATE_ACCEPTED')
 with (k/'o'/(job+'.canary.json')).open('x') as handle:
  json.dump(record,handle,sort_keys=True);handle.write('\n')
P
TZ=UTC env -u TK_JOB_START sbatch -J a15_cot_ap0f5aa514 -o /dev/null -e "$KH/o/%j.err"   -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 13:00:00 --signal=B:USR1@3600 --no-requeue "$BUN/jb.sh"
