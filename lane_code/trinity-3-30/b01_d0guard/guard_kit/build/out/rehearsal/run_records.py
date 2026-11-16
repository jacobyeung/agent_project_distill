"""Recorded-row control-flow rehearsal. This never loads or decodes a model."""
import argparse
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
B=Path(__file__).resolve().parents[2];sys.path.insert(0,str(B/'out/guard_kit'))
from guard_core import read,write,sha,pipeline,rows_in_order

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--mismatch',action='store_true');a=p.parse_args()
 out=Path(a.out).resolve()
 if not out.is_relative_to(B):raise ValueError('Output must remain in the build')
 out.mkdir(parents=True,exist_ok=False)
 ref=read(B/'out/inputs/reference.json');inputs=read(B/'out/inputs/items.json')
 source=B.parents[1]/'guard_kit/report/tests/fixtures/R1_544_COMPACT.json'
 fixture=read(source);by={r['key']:r for r in fixture['arms']['unflagged']};calls=[];published=[]
 def publish(path):
  target=out/'published'/path.name;target.parent.mkdir(exist_ok=True);target.write_bytes(path.read_bytes())
  if sha(target)!=sha(path):raise ValueError('Local publication digest differs')
  published.append(path.name)
 def proof_reader(keys):return deepcopy(ref)
 expected=deepcopy(ref)
 if a.mismatch:expected[0]['decode']['tokens'][0]+=1
 def candidate(keys):
  calls.append(keys)
  if len(calls)>1 and 'CANARY.json' not in published:raise ValueError('Full arm preceded canary publication')
  return [deepcopy(by[k]) for k in keys]
 result=dict(fixture=True,whole_worker_complete=False,actual_model_decode=False,
             boundary='Recorded accepted rows; no stage, restoration, geometry or model computation',
             config_changed_only_in_transport=False,source=str(source),source_sha256=sha(source))
 try:
  bundle=pipeline(expected,proof_reader,candidate,inputs['keys'],inputs['canary_keys'],out/'run',publish,fixture=True)
  rows_in_order(bundle['arms']['unflagged'],inputs['keys'])
  archive=out/'result.tar'
  with tarfile.open(archive,'w',format=tarfile.USTAR_FORMAT) as t:
   for name in ('PROOF.json','CANARY.json','R1.json'):
    data=(out/'run'/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0;t.addfile(info,io.BytesIO(data))
  fetched=out/'fetched.tar';fetched.write_bytes(archive.read_bytes())
  if sha(fetched)!=sha(archive):raise ValueError('Local fetch digest differs')
  report=B.parents[1]/'guard_kit/report/guard_read.py';before=sha(report)
  command=[sys.executable,'-I','-s','-B',str(report),'--candidate',str(out/'run/R1.json'),
           '--step544',str(out/'run/R1.json'),'--out',str(out/'report')]
  with (out/'report.log').open('w') as log:
   completed=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=False)
  if sha(report)!=before:raise ValueError('Report source changed')
  result.update(status='PASS' if completed.returncode==0 else 'FAIL',report_returncode=completed.returncode,
                report_sha256=before,report_argv=command,report_comparison='Recorded-row fixture against itself',
                archive_sha256=sha(archive),fetched_sha256=sha(fetched),candidate_items=sum(map(len,calls)))
 except Exception as error:
  result.update(status='EXPECTED_REFUSAL' if a.mismatch and not calls else 'FAIL',error=str(error),candidate_items=sum(map(len,calls)),
                proof_receipt=(out/'run/PROOF.json').is_file(),candidate_arm_exists=(out/'run/R1.json').exists())
 result['published']=published;write(out/'RESULT.json',result)
 print(json.dumps(result,indent=2))
 return 0 if result['status'] in ('PASS','EXPECTED_REFUSAL') else 1
if __name__=='__main__':sys.exit(main())
