from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import tarfile
import time

L=Path('/scratch/jjyeung/orch_n30/so_syncfix')
source=L/'work/round1'
out=L/'out'
logs={name:(source/'logs'/('py%s_final.txt'%name)).read_text() for name in ('36','312')}
for name,text in logs.items():
    assert re.search(r'Ran 55 tests in [0-9.]+s\n\nOK\n',text), name
for name in ('36','312'):
    assert 'FAILED (failures=13)' in (source/'logs'/('before_py%s.txt'%name)).read_text()

def match(pattern,name):
    return re.search(pattern,logs[name]).groups()

measure={}
for name in logs:
    measure[name]={
        'suite':match(r'Ran 55 tests in ([0-9.]+)s',name)[0],
        'manifest':match(r'large_manifest lines=(\d+) raw_bytes=(\d+) gzip_bytes=(\d+) elapsed=([0-9.]+)s',name),
        'node':match(r'held_stdout_node_elapsed=([0-9.]+)s',name)[0],
        'driver':match(r'held_stdout_driver_elapsed=([0-9.]+)s',name)[0],
        'slots':dict((label,json.loads(amounts)) for label,amounts in re.findall(r'MEASURE slot=(\S+) bytes=(\{[^\n]+?\}) total=\d+',logs[name])),
        'failed':match(r'failed_slot=trinity-1-18 incoming_bytes=(\d+) accepted_bytes=(\d+)',name),
    }
rows=[['Check (measured)','Python 3.6.8','Python 3.12.13'],['---','---:','---:'],
      ['Complete functional suite','55 passed, 0 skipped','55 passed, 0 skipped'],
      ['Suite duration',measure['36']['suite']+' s',measure['312']['suite']+' s'],
      ['Large manifest lines',measure['36']['manifest'][0],measure['312']['manifest'][0]],
      ['Large manifest uncompressed bytes',measure['36']['manifest'][1],measure['312']['manifest'][1]],
      ['Large manifest gzip bytes',measure['36']['manifest'][2],measure['312']['manifest'][2]],
      ['Large manifest test duration',measure['36']['manifest'][3]+' s',measure['312']['manifest'][3]+' s'],
      ['Held-writer node duration (0.35 s + 0.15 s grace)',measure['36']['node']+' s',measure['312']['node']+' s'],
      ['Complete held-writer driver duration',measure['36']['driver']+' s',measure['312']['driver']+' s'],
      ['Partial source failure','1 fake commit; 2 fake pushes; prior files preserved','1 fake commit; 2 fake pushes; prior files preserved']]
results='\n'.join('| '+' | '.join(row)+' |' for row in rows)
rows=[['Source slot','Accepted archive bytes (3.12 fixture)','Total slot bytes (3.6 fixture)','Total slot bytes (3.12 fixture)'],['---','---:','---:','---:']]
for label in ('trinity-1-18','trinity-2-28','trinity-3-30','orch_n30/tools','orch_n30/briefs'):
    rows.append([label,str(measure['312']['slots'][label]['accepted']),str(sum(measure['36']['slots'][label].values())),str(sum(measure['312']['slots'][label].values()))])
slots='\n'.join('| '+' | '.join(row)+' |' for row in rows)
slots+='\n\nThe failed trinity-1-18 attempt retained `incoming=%s` and `accepted=%s` bytes on both interpreters. The two archive slots therefore held %d bytes in that failure fixture.' % (*measure['312']['failed'],sum(int(x) for x in measure['312']['failed']))
assert measure['36']['failed']==measure['312']['failed']
summaries='\n\n'.join('Python '+version+':\n\n```text\n'+re.search(r'Ran 55 tests.*\n\nOK',logs[name]).group(0)+'\n```' for name,version in [('36','3.6.8'),('312','3.12.13')])
report=(source/'REPORT.template.md').read_text().replace('__RESULTS__',results).replace('__SLOTS__',slots).replace('__EXACT_SUMMARIES__',summaries).replace('__PREIMAGE__',(source/'PREIMAGE.sha256').read_text().rstrip())
assert '__RESULTS__' not in report
(source/'REPORT.md').write_text(report)

# Populate only deliverables; intermediate development logs stay in work/.
for folder in ('tools','tests','inputs','patches','evidence'):
    (out/folder).mkdir(exist_ok=True)
    for path in (source/folder).iterdir():
        if path.is_file():
            (out/folder/path.name).write_bytes(path.read_bytes())
for name in ('REPORT.md','INSTALL_TOOLS.diff','PREIMAGE.sha256','POSTIMAGE.sha256','install_tools.py','calibrate_budgets.py'):
    (out/name).write_bytes((source/name).read_bytes())
(out/'logs').mkdir(exist_ok=True)
for name in ('py36_final.txt','py312_final.txt','before_py36.txt','before_py312.txt','delivery_before_py36.txt','delivery_before_py312.txt','package_check.txt'):
    (out/'logs'/name).write_bytes((source/'logs'/name).read_bytes())
# Stable manifest membership before the artifact tests populate their output.
for name in ('delivery_py36.txt','delivery_py312.txt'):
    if not (out/'logs'/name).exists(): (out/'logs'/name).write_text('Artifact verification follows packaging.\n')

# Check every shell block in the report without executing installation/calibration.
blocks=re.findall(r'```bash\n(.*?)```',report,re.S)
for i,block in enumerate(blocks):
    result=subprocess.run(['bash','-n'],input=block.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert result.returncode==0,(i,result.stderr)
print('PASS: %d report shell blocks parse.'%len(blocks))
# Copy static audit decisions into the evidence ledger, not into code comments.
assert (out/'tools/sync_health.py').read_bytes()==(out/'inputs/sync_health.py').read_bytes()
original=(out/'inputs/lane_code_filter.py').read_text()
candidate=(out/'tools/lane_code_filter.py').read_text()
assert candidate[candidate.index('\nlabel = sys.argv'):]==original[original.index('\nlabel = sys.argv'):]
original=(out/'inputs/lane_code_scan.py').read_text()
candidate=(out/'tools/lane_code_scan.py').read_text()
body=candidate[candidate.index('stage, dest, flagout = sys.argv[1:4]'):]
branch="if os.environ.get('LCS_ROBUST_SYNC', '0') == '1':\n    robust_copy_scan(stage, dest, flagout)\n    sys.exit(0)\n\n"
body=body.replace(branch,'',1)
assert body==original[original.index('stage, dest, flagout = sys.argv[1:4]'):]
(out/'evidence/default_path_audit.txt').write_text('PASS: legacy filter body is byte-identical.\nPASS: legacy scanner body is byte-identical after excluding the explicit robust branch.\nPASS: sync_health.py is byte-identical.\nPASS: report shell blocks parse.\n')
print('PASS: legacy bodies and unchanged health tool match the inputs.')
print(json.dumps(measure,sort_keys=True))
