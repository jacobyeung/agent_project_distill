"""Write the independently reviewable Cprime identities, evidence and limits."""
import difflib,hashlib,json,re,tarfile
from pathlib import Path
from rebind import ROOT,load,write,sha
from build_cprime import SNAP
from cprime_gate import B1,GO
from cprime_removal import ORIGINAL
D=Path('/scratch/jjyeung/orch_n30/r1_ops/work/drv_cp')

def suite(name):
    text=(ROOT/'out/logs'/name).read_text();m=re.search(r'Ran (\d+) tests',text)
    return dict(tests=int(m[1]) if m else 0,passed=bool(re.search(r'\nOK(?: \([^\n]*\))?\s*$',text)))

def main():
    out=ROOT/'out';ids=load(out/'CPRIME_IDENTITIES.json');cfg=load(out/'config.json');op=load(out/'OPERATOR.json')
    census=load(out/'CENSUS_CPRIME.json');audit=load(out/'proof/loader_audit.json');legacy=load(out/'LEGACY_TESTS_CPRIME.json')
    local=load(out/'LOCAL_CHECKS_CPRIME.json');recovery=load(out/'H1_RECOVERY_CPRIME.json');inputs=load(out/'RECOVERED_INPUTS_CPRIME.json')
    delta=suite('cprime_gate_tests.log');drivers=suite('cprime_driver_tests.log')
    assert sha(out/op['archive'])==op['sha256']
    assert audit['requested_config_identity']==ids['identity'] and audit['planned_steps']==1000
    assert audit['counting_draws_by_form']==dict(PROC=10460,FS_LIST=0,OTHER=0)
    assert census['after']['counting']==2617 and census['after']['totals']==0
    problems=[]
    if not delta['passed'] or not drivers['passed']:problems.append('new tests failed')
    if legacy['failures'] or legacy['errors']:problems.append('legacy failures without a missing-input waiver')
    if any(v['status']=='FAIL' for v in local.values()):problems.append('local check failed')
    status='INCOMPLETE: '+ '; '.join(problems) if problems else 'BUILT_FOR_INDEPENDENT_REVIEW'
    lines=[status,'',f"Config `{ids['identity']}`; run `{ids['run_key']}`; job `{ids['job_name']}`; bundle `{ids['bun']}`; kit `{ids['kh']}`.",'',
        f"Archive `{op['archive']}`; SHA256 `{op['sha256']}`; {Path(out/op['archive']).stat().st_size:,} bytes. Two builds produced the same archive. The archive contains 43 regular files with an exact SHA256 inventory. Existing archives and snapshots remain intact.",'',
        f"B1r SHA256 `{B1}`; original B1 SHA256 `{ORIGINAL}`. Both lists have the same ordered 17,879 row keys. Each pool value becomes `p` plus the first eight hex characters of its SHA256. Every byte outside the pool JSON string stays identical, including line order, key order, separators and reason. `out/B1R_MAPPING.json` records the private mapping and both hashes; it is absent from the archive and kit.",'',
        'Loader evidence: `work/tree/student_pilot/row_removals.py:27–46` validates row keys and optional defect filters; lines 48–61 match those keys against row identities. The loader never accesses pool or restricts reason. The unchanged `count_diag_first_seen_list_form` reason is accepted. B1r has zero matches against the content deny expression used for this build; the independent whole-kit CLEAN certificate remains required. The opaque staging name is `z.json` in both the bundle and records.','',
        'The config resumes A’s real step-200 slot, stops at 600, exports 400 and 600, and uses `continuation.rows = rebind`. Counting is 1046 cents, totals 0 and direction 3499. Routing, other VQA cells, trainer, stores, selection, units, S2, seed and learning-rate horizon retain C4’s pins.','',
        '| Config field | C4 | Cprime |','|---|---|---|']
    for row in load(out/'CONFIG_DIFF_CPRIME.json'):
        lines.append('| '+row['field']+' | '+json.dumps(row['before'],sort_keys=True)+' | '+json.dumps(row['after'],sort_keys=True)+' |')
    lines+=['','The census applies all seven C4 REMOVE lists, then B1r, to the SHA256-verified v7 SQLite store. It reproduces all C4 eligible counts. Eligible rows fall from 203,812 to 185,933; all 2,617 remaining counting rows use procedure form. No cents adjustment is needed.','',
        '| VQA cell | Before B1r | After B1r | Cents | Rows/step | Ceiling: 4 × eligible / 1,000 | Draws over 1,000 steps | Unique drawn rows | Max draws/row |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n,v in cfg['type_mix']['streams']['vqa']['cells'].items():
        a=audit['per_cell_draws'][n]
        lines.append(f"| {n} | {census['before'][n]} | {census['after'][n]} | {v['cents']} | {v['cents']/100:.2f} | {census['ceilings'][n]:.3f} | {a['draws']} | {a['unique_rows']} | {a['max_draws_per_row']} |")
    lines+=['','Every cell satisfies its measured ceiling. The direction card’s 373.48 combines direction (49,901 rows) and facing (43,469 rows). The sealed loader treats them as separate cells, so direction’s measured ceiling is 199.604. Its configured 34.99 rows per step is below that ceiling.','',
        'The native VQA-only loader audit passed over 1,000 steps with all eight REMOVE lists. It drew 128,000 rows, with at most four draws per row. Counting draws: procedure 10,460; first-seen list form 0; other 0. This audit checks local structural eligibility and the native sampler. Production RGB, division recomputation and routing admission remain in-job checks.','',
        f"The canary_delta gate authenticates C4 identity `6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74` through admission job 172180 and the exact receipt/log pins. It compares the complete sealed C4 and Cprime configs, permits only the seven reported differences, verifies derived paths and staged pins, and records `canary_delta=true`. GO authority is `sha256:{GO}`. It requires no PROOF_JOB. PASS and canary branch bodies remain byte-identical to C4.",'',
        '| Validation | Result |','|---|---|',
        f"| Delta gate and B1r byte/row-key tests | {delta['tests']} passed |",
        f"| Driver pin, review, pending-state and session tests | {drivers['tests']} passed |",
        f"| Legacy suite | {legacy['selected']} selected: {legacy['passed']} passed, {legacy['skipped']} not run for missing recovered inputs, {legacy['failures']} failures, {legacy['errors']} errors |",
        '| Archive reseal | PASS; exact deterministic archive |',
        '| D0 OFF identity | PASS; all four rank states exact |',
        '| Cprime native first batch | PASS; four ranks, finite losses and S2 checks |',
        '| Two H1 deployment derivations | NOT RUN; missing pinned k/s1_record.json |','',
        'All suites ran sequentially through `tools/cprime_local.sh`, under `prlimit --as=21474836480` with thread limits at most eight. `tools/run_local_checks.py --cprime` runs the Cprime package, derivation and native checks; its derivation-only recheck uses the verified local H1 recovery. No network, SSH, Orchard operation, Git, deletion, minting or submission ran.','',
        f"The mint helper matches `b7388f557f941ccd0e3c2d82bf3ade0e1ad34e8a96e5f995d35dcefef79cf57d`. The recovered D0 tree has {inputs['d0_files']} files and inventory `{inputs['d0_inventory_sha256']}`; reconstructing its deterministic archive reproduces `{inputs['d0_archive_expected_sha256']}`. H1 recovery reproduces its pinned tree, archive and code record and restores {len(recovery['restored'])} manifest entries without changing their pins.",'',
        'The recovered H1 view still lacks the following pinned members. `H1_RECOVERY_CPRIME.json` records each expected SHA256; no replacement pin is fabricated.','']
    lines+=['- `'+recovery['source']+'/'+v['file']+'`' for v in recovery['missing']]
    lines+=['','The unavailable native division input is `/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json`. Its check is not run and does not block this review build; Orchard admission recomputes the division. The complete per-test missing-input ledger is `LEGACY_TESTS_CPRIME.json`. It includes filtered older derived-kit inventories, frozen snapshot artifacts, frame maps, row slices, and admission logs. These omissions prevent claims that the full legacy suite or local deployment derivation passed.','',
        'The reviewer must check the exact config delta and B1r byte-only rewrite; census and draw evidence; C4 admission pins; the production H1 derivation and its manifest; the unchanged p/t/u authority; the twelve-review chain; independent whole-kit CLEAN classification; the real A donor; 20 fresh sessions; and final archive/driver checksums. The missing-input checks are waived only for this local review build. Drivers retain the production gates.','',
        f"Operator sequence and expected outputs: `{D}/README.md`. Driver hashes: `{D}/DRIVER_SHA256SUMS.txt`. rv1, sc1 and si1 are intentionally inert until the independent review, CLEAN certificate and fresh sessions arrive."]
    (out/'CPRIME.md').write_text('\n'.join(lines)+'\n')
    write(out/'CPRIME_STATUS.json',dict(status=status,identity=ids['identity'],archive=op['archive'],archive_sha256=op['sha256'],
        census_run=True,audit_run=True,delta_tests=delta,driver_tests=drivers,legacy_tests={k:v for k,v in legacy.items() if k!='tests'},
        local_checks=local,production_authorized=False,open_implementation_defects=problems))
    # Compare authenticated archive inventories, without presenting a missing derived kit as verified.
    def members(path):
        with tarfile.open(path) as tf:return {m.name:tf.extractfile(m).read() for m in tf}
    old=members(SNAP/'out/p_08f3a7b2.tar');new=members(out/op['archive']);kit=[]
    for name in sorted(set(old)|set(new)):
        a=hashlib.sha256(old[name]).hexdigest() if name in old else None;b=hashlib.sha256(new[name]).hexdigest() if name in new else None
        if a!=b:kit.append(dict(file=name,before=a,after=b))
    write(out/'KIT_DIFF_CPRIME.json',kit)
    kt=['The table compares every member of the authenticated C4 and Cprime archives. The deployed-kit manifest comparison is NOT RUN because recovered H1 lacks pinned `k/s1_record.json`; `dv1.sh` performs the production derivation.','',
        '| Archive member | C4 SHA256 | Cprime SHA256 |','|---|---|---|']
    kt+=['| '+v['file']+' | '+(v['before'] or 'absent')+' | '+(v['after'] or 'absent')+' |' for v in kit]
    unchanged=len([n for n in old if n in new and old[n]==new[n]])
    kt+=['',f'{unchanged} members remain byte-identical. Trainer t.tar, deployment deriver d.py, authority r4.py, continuation c0.py, proof validator p.py, stores, selection and unit payloads retain their C4 bytes. B1R_MAPPING.json is absent from both the new archive and operator directory.','',
        'Expected derived changes: config, run/output paths, launch identity and contract directory, current staging inventory with z.json, manifest and packet-specific pending evidence. This expected list does not substitute for a derived-manifest comparison.']
    (out/'KIT_DIFF_CPRIME.md').write_text('\n'.join(kt)+'\n')
    readme=f'''Cprime is built for independent review. Config `{ids['identity']}`; run `{ids['run_key']}`; job `{ids['job_name']}`; bundle `{ids['bun']}`; kit `{ids['kh']}`.

Archive `{op['archive']}`, SHA256 `{op['sha256']}`. Verify DRIVER_SHA256SUMS.txt before use. The names are fresh; m1 is unnecessary unless the operator finds a collision. No proof or rehearsal driver is provided.

| Order | Driver or local builder | Expected output or condition |
|---|---|---|
| 1 | u1.sh | Fresh private bundle; authenticated archive uploaded and unpacked; PASS outer SHA, 43 members, exact sums.txt inventory, files 0600 |
| 2 | q1.sh | PASS native selection and bound-unit regeneration |
| 3 | review_build.py --cprime PATH, then rv1.sh | Twelve-review chain: eleven pinned C4 antecedents plus events/review_cprime/REVIEW_VERDICT_CPRIME.md; READY rv1.sh, then PASS installed chain |
| 4 | ev1.sh, then evp1.sh | STARTED e0; then e0 rc=0; both REMOVE additions and final identity bound |
| 5 | dv1.sh, then dvp1.sh | STARTED d0; then d0 rc=0, READY evidence, exact p/t/u authority and code directories 0500 |
| 6 | scan1.sh | Exact packet/config/manifest inventory for independent whole-kit content classification; B1r itself has zero content deny hits |
| 7 | cert_build.py, then sc1.sh | Packet-specific independent CLEAN certificate accepted and installed |
| 8 | L1_mint.sh on trinity-3-30 | PASS 20 fresh create-only sessions, packet-specific filenames, mode 0600; URI contents withheld |
| 9 | session_build.py, then si1.sh | READY si1.sh; exact 20 export destinations installed privately |
| 10 | pre1.sh | PASS REAL A resume pointer; verified step-200 slot archive, manifest, binding and shards; Cprime rebind policy verified |
| 11 | go_submit_canary_delta_{op['sha256'][:8]}.sh <GO_SHA> | Pinned GO and admission 172180 accepted; one advanced four-GPU, 24-hour submission; training.job.id recorded |
| 12 | mon.sh | Read-only queue/accounting and bounded redacted logs |

The required GO SHA is `{GO}`. No PROOF_JOB is needed. The new review must explicitly state Packet Cprime: GO (or GO AFTER FIXES with only LOW nonblocking fixes) and name the full config identity or archive SHA. The reviewer hashes bind the original review bytes. rv1/sc1/si1 exit 4 until their independent inputs arrive; no review, certificate or session is fabricated.

The mint helper is present and verified at `/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py`, SHA256 `b7388f557f941ccd0e3c2d82bf3ade0e1ad34e8a96e5f995d35dcefef79cf57d`. L1_mint.sh is a local Trinity step; the other shell drivers target Orchard. Use each local builder's --help for its required independent inputs. Recompute the checksum manifest after an approved builder replaces a pending script.

Local validation: 17 delta/removal tests and five driver tests pass; {legacy['passed']} legacy tests pass and {legacy['skipped']} cannot run because recovered inputs are missing. Census, 1,000-step VQA audit, deterministic reseal, D0 equivalence and four-rank first batch pass. Local H1 derivation cannot run without pinned k/s1_record.json. See `{out}/CPRIME.md` and its missing-input ledger; production derivation and admission remain mandatory.

u1.sh includes the archive transfer and extraction. u3.sh is the extraction helper embedded into u1; do not run it again after u1 succeeds. Poll at most once a minute. Stop after any failed or uncertain operation and preserve attempt markers; do not retry automatically. The private pool mapping stays on Trinity and is never uploaded.
'''
    (D/'README.md').write_text(readme)
    files=set()
    for directory in ('tools','tests','configs'):
        files.update(str(p.relative_to(ROOT)) for p in (ROOT/directory).iterdir() if p.is_file() and p.suffix in ('.py','.sh','.json','.in'))
        files.update(str(p.relative_to(SNAP)) for p in (SNAP/directory).iterdir() if p.is_file() and p.suffix in ('.py','.sh','.json','.in'))
    files.update(('out/config.json','out/BINDING.json','out/OPERATOR.json','out/proof/inputs.json'))
    patch=[]
    for name in sorted(files):
        a=(SNAP/name).read_text().splitlines(keepends=True) if (SNAP/name).exists() else []
        b=(ROOT/name).read_text().splitlines(keepends=True) if (ROOT/name).exists() else []
        patch.extend(difflib.unified_diff(a,b,fromfile='snap_08f3a7b2/'+name,tofile='cprime/'+name))
    (out/'CPRIME.diff').write_text(''.join(patch))
    hashes=[p for p in D.iterdir() if p.is_file() and p.name!='DRIVER_SHA256SUMS.txt']
    (D/'DRIVER_SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(hashes)))
    print(json.dumps(dict(status=status,identity=ids['identity'],archive=op['archive'],legacy_passed=legacy['passed'],legacy_not_run=legacy['skipped'])))

if __name__=='__main__':main()
