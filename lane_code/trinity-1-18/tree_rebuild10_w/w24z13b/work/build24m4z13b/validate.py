from pathlib import Path
import csv,json,hashlib,os,sys
J=Path(__file__).resolve().parents[2];W=J/'work/build24m4z13b'
rows=json.loads((W/'results.json').read_text());assert len(rows)==52,len(rows)
assert all(r['PASS'] for r in rows)
assert (W/'extra.log').read_text().endswith('PASS: 52 total cases\n')
assert (W/'tests.log').read_text().endswith('PASS: 38 cases; pristine source and kit unchanged\n')
assert json.loads((W/'fallback_bound/result.json').read_text())['status']==3
for r in rows:
    if r['version']=='5':
        assert r['status']==r['expected'] and r['once']==1 and r['published'] and r['periodic_stopped'],r
        files=json.loads((J/r['log']/'published.json').read_text())
        if 'j2.fallback.log' in files:
            assert 'P79' not in files['j2.fallback.log']
            assert len(files['j2.fallback.log'].splitlines())==1
# Check only the known PIDs launched by this suite; never scan unrelated jobs.
active=[]
for events in W.glob('*/events.jsonl'):
    for e in map(json.loads,events.read_text().splitlines()):
        p=Path('/proc')/str(e['pid'])/'stat'
        try:
            if p.exists() and p.read_text().split()[2]!='Z':active.append(e)
        except FileNotFoundError: pass
assert not active,active
assert (W/'source.before.json').read_bytes()==(W/'source.after.json').read_bytes()
prior=json.loads((J/'work/build24m4z13/source.before.json').read_text())
assert prior==json.loads((W/'source.before.json').read_text())
# Fresh bounded digest audit of the original kit supplied to the lane.
source=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n')
actual={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.rglob('*')) if p.is_file()}
assert actual==prior
with (W/'test_table.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=['case','version','status','expected','once','published','periodic','periodic_stopped','ticks','watchdog','seconds','token','log','PASS'])
    writer.writeheader();writer.writerows(rows)
labels=sorted({r['case'] for r in rows});index={(r['case'],r['version']):r for r in rows}
lines=['Each row compares the supplied jn4 bytes with jn5 after only private X/pool substitutions.',
       'Healthy publication rows are regression controls; setup and publisher-fault rows demonstrate fail-before/pass-after.',
       'The baseline hang is intentionally stopped by the test watchdog. It is not a cluster-killed job.',
       'The periodic worker is the generated j2.py itself; setsid is not replaced. The ticks case shortens only its interval argument.',
       'TERM/USR1 cases signal the wrapper and verify delivery to all three real child processes, child reaping, status, and one final attempt.',
       'The real resolver sees an empty pool. The real l.py receives a read-only stdout descriptor and fails under pipefail.',
       'The setup cases fail directory creation, log redirection, and publisher creation. The node case fails before N exists.',
       'The main publication blocks in an actual FIFO open. GNU timeout uses its full 120-second deadline; fallback then writes the fixed refusal.',
       'The separate blocked-fallback check intentionally cannot publish; its 15-second deadline preserves status 3.',
       'The initial harness assertion included j2.log.part as a committed output. Its output is in first_failure.log; complete frozen artifacts are in attic/attempt1.',
       'Original source kit hashes match both the supplied manifest and the fresh audit. No suite process remains running.',
       'No scheduler, live Slurm signal delivery, deployed Orchard bytes, or production workload shutdown was tested.',
       'The forbidden-name screen accepts every fixed fallback label and new submission name.',
       'No historical narrative was retained in the usage notes except required test-failure evidence and the explicit jn4 comparison.',
       '', '| Case | jn4 status / final / named output | jn5 status / final / named output |', '|---|---|---|']
for label in labels:
    a=index[label,'4'];b=index[label,'5']
    fmt=lambda r:f"{r['status']} / {r['once']} / {r['published']}"
    lines.append(f'| {label} | {fmt(a)} | {fmt(b)} |')
(W/'VALIDATION.txt').write_text('\n'.join(lines)+'\n')
sha=hashlib.sha256((J/'out/jn5.sh').read_bytes()).hexdigest()
report=[f'jn5.sh SHA-256: `{sha}`. All 52 cases (26 jn4/jn5 pairs) and the separate fallback-bound check passed their stated assertions.',
'| Check | jn4 → jn5 | Evidence under work/build24m4z13b/ |',
'|---|---|---|',
'| Setup; failing/caught-error publisher; resolve and l.py faults | Missing named refusal → fixed fallback; status preserved; one final attempt | tests.log, extra.log, test_table.csv |',
'| Blocked final publisher / blocked fallback | jn4 watchdog at 124.285 s → jn5 refusal at 120.237 s; blocked fallback returns at 15.240 s; status 3 | hang_4/, hang_5/, fallback_bound/ |',
'| GPU/seal/resolve/l.py controls; periodic ticks; child-tree TERM/USR1; final-publish signals | Controls pass; injected faults fail before and pass after; jn5 preserves status and makes one final attempt | results.json, VALIDATION.txt |',
'| Header/ROOT/forwarding; source-kit hashes; fixed-text screening; syntax | PASS; no live Slurm/Orchard test. Initial harness assertion/output retained. | static_checks.log, source.before.json, source.after.json, first_failure.log |']
report[0]+=' Header/ROOT/forwarding, source hashes, screening and syntax pass; no live Orchard test.'
report[5]=report[5].replace('results.json, VALIDATION.txt','results.json, VALIDATION.txt, static_checks.log; initial harness failure output: first_failure.log')
report=[report[0],'']+report[1:6]
assert len(report)<8
(J/'out/BUILD24M4Z13B_REPORT.md').write_text('\n'.join(report)+'\n')
print('PASS: 52 cases (26 jn4/jn5 pairs) + 1 blocked-fallback case; no suite processes remain; original kit hash audit; report has 7 lines')
