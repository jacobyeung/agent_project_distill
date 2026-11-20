from common import *
import subprocess
F=D/'discovery_shell_protected_bytes';k=F/'kit';node=F/'nodes/q_22c714e1_94'
for rel in ('b/h.py','b/rv.py','b/cs.py','b/sv.py'):replace(k/rel,(kit('qd')/rel).read_bytes())
for rel in ('BUILD.json','SHA256SUMS.txt'):replace(k/rel,(k/rel).read_bytes())
reseal(k)
prefix=(F/'staged.sh').read_text().split('# Both invocations')[0]
script=F/'final_review.sh'
script.write_text(prefix+'''
"$BW" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/h.py" "$Q_NS/p" "$Q_NS/v.json"
"$BW" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/rv.py" "$Q_NS" "$Q_NS/v.json" "$SLURM_JOB_ID"
'''.replace('"$BW"','"'+chr(36)+'{BW[@]}"'))
r=subprocess.run(['/bin/bash',str(script)],capture_output=True,text=True,env={**os.environ,'SLURM_JOB_ID':'94'})
(F/'final_review.log').write_text(r.stdout+r.stderr);assert r.returncode==0,(r.stdout,r.stderr)
live=F/'target/o/94/live';cfg=J.load(node/'v.json');host=J.load(live/'h0.json')
assert J.sha(live/'h0.json')==cfg['r1_training']['host_receipt']['sha256']
assert J.sha(live/'c4.json')==host['protected_census']['sha256']==J.sha(node/'c5.json')
assert J.load(live/'c4.json')['streams']['pointing']['status']=='WOULD_REFUSE'
assert (live/'WAITING_REVIEW.json').is_file() and not (live/'REVIEW_ACCEPTED.json').exists()
J.write(D/'HOST_REVIEW_TESTS.json',dict(status='PASS',h_and_rv_actual=True,host_receipt_published_byte_identical=True,census_published_byte_identical=True,pointing_would_refuse=True,stops_at='WAITING_REVIEW',GO=False,claims='nothing',kit_helper_hashes={f:J.sha(kit('qd')/'b'/f) for f in ('h.py','rv.py','cs.py','sv.py')}))
print('Actual h/rv verify published host and census pins; qd WOULD_REFUSE continues PASS')
