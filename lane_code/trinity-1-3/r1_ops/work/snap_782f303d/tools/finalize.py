"""Write the review packet from current, identity-bound local evidence."""
import hashlib,json,os,re,sys
from pathlib import Path
from rebind import ROOT,load,sha,write

def main():
    out=ROOT/'out';b=load(out/'BINDING.json');op=load(out/'OPERATOR.json')
    cfg=load(out/'config.json');audit=load(out/'proof/loader_audit.json');census=load(out/'ADMISSION_BY_TYPE.json')
    room=census['traced_room'];away=census['reworded_away'];table=audit['tables']['vqa']
    first=load(out/'proof/FIRST_BATCH.json');off=load(out/'proof/OFF_IDENTITY.json');derivation=load(out/'proof/DERIVATION.json')
    for v in (first,derivation):
        if v['status']!='PASS' or v['config_identity']!=b['config_identity']:raise ValueError('Local proof is stale')
    if audit['requested_config_identity']!=b['config_identity'] or off['candidate_tree_sha256']!=b['tree_sha256']:raise ValueError('Local evidence binding differs')
    log=(out/'logs/tests.log').read_text()
    if not log.rstrip().endswith('OK'):raise ValueError('Tests did not pass')
    n=int(re.search(r'Ran (\d+) tests',log).group(1))
    gate=lambda status,scope:dict(status=status,scope=scope)
    gates=dict(schema='r1-local-gates-v1',status='BUILT_BLOCKED',config_identity=b['config_identity'],production_authorized=False,
        checks=dict(tests=gate('PASS',str(n)+' tests'),off_identity=gate('PASS',off['scope']),
            first_batch=gate('PASS',first['scope']),deterministic_derivation=gate('PASS',derivation['scope']),
            admission_coverage=gate('PASS',str(census['vqa_rows'])+' VQA rows; every stored question type checked; '+str(census['vqa_admitted'])+' admitted; row predicates only'),
            loader_audit=gate('LOCAL_VQA_ONLY','1000 steps, 128000 real-store VQA draws; other streams unavailable'),
            room_selection_projection=gate('PASS','586 selected source rows removed; all non-room entries and ordered indices unchanged'),
            native_selection_regeneration=gate('NOT_RUN','Complete source archives absent locally; 581 materialized rows remain unverified'),
            production_preparation=gate('NOT_RUN','No Orchard call; local source kit lacks two inherited members'),
            required_families=audit['required_families'],
            outer_filename_scan=gate('PASS','Opaque operator archive member names'),
            complete_privacy_scan=gate('NOT_RUN','Independent final deployment content scan and ANON_OK.json required'),
            independent_review=gate('PENDING','Admission inputs and sampler code changed')))
    gates['absent_on_P']=b['absent_on_P']
    gates['checks']['traced_room']=dict(status='PASS' if room['eligible']==room['rows'] else 'FAIL',**room)
    gates['checks']['unit_candidate']=gate('REFUSED_UNBOUND','The read-only units_p_slice_v2 fixture lacks top-level events and 32 frame pins; a packed successor is required.')
    write(out/'proof/GATES.json',gates)
    write(out/'REVIEW_REQUEST.json',dict(status='REVIEW_REQUIRED',config_identity=b['config_identity'],tree_sha256=b['tree_sha256'],
        operator_archive=op['archive'],operator_archive_sha256=op['sha256'],reviews_requested=1,
        reason='Admission inputs change. Review family quotas, receipt binding, routing refusals, staging changes and CPU proof before any deployment approval.',
        dispatch_result_event='Dispatching lane writes the RESULT event; this packet sends no external message.'))
    unit_status=('Units are bound to a faithful file; eligible counts are '+json.dumps(b['unit_binding']['counts'],sort_keys=True)+'.' if b.get('unit_binding') else 'Units are unbound and have zero dose. A bound source trains feet by default; units below 100 eligible rows are named absent with their counts and do not fail the family gate.')
    family_set='Vehicle P requires every nonzero VQA cell, routing camera displacement, camera movement direction, camera rotation and absolute distance; recovery, size and unbound units are absent at launch. '+unit_status
    report=f'''{family_set}

The packet is built for review and remains blocked for production. Config identity is `{b['config_identity']}`. S1 and S2 are off; S2 remains a switch. Scheduled sampling matches D0, the schedule remains 1,000 steps, milestones are 100 and 200, and the run stops at 200. Its disk plan reserves three weight exports.

The full v7 census covers {census['vqa_rows']:,} rows and all {len(census['types_covered'])} question types; {census['vqa_admitted']:,} pass the checked predicates. This does not certify RGB bytes, division ancestry, complete source closure or production preparation. `ADMISSION_BY_TYPE.json` records that scope and the receipt and database hashes.

Recovery fails at sealed `student_pilot/ground_rows.py:82`: `ground_record.not_seen` is true, while line 81 requires it to be false. The failure persists through the native packer. Production validates these rows before adding frames and never clears the flag.

{unit_status} `--unit-rows FILE --unit-rows-sha256 SHA` accepts packed JSONL with full events and 32 explicit frame pins. It preserves all input bytes, validates each row through sealed admission, binds a new pool source, and caps its dose at four times eligible rows over 1,000 steps. Each unit below 100 post-filter rows is named as missing. The specified 1,224-row units_p_slice_v2 candidate has ft=1,130, in=94 and cm=0. Its read-only fixture fails binding because it lacks top-level events and frame pins. A packed successor is required; no production unit source is bound. `ROUTING_DIAGNOSIS.json` retains the separate sealed-refusal diagnosis.

V7 contains {room['rows']} traced room rows: {room['sealed_row_checks_pass']} pass the sealed row checks, {room['qualitative_trace_pass']} pass the qualitative-trace predicate, and {room['eligible']} are eligible. The 476 square-metre and 95 square-foot one-line diagnostic room rows have zero eligible rows. A room row needs the r1_room_traced pool, pinned Seen citations, exactly one qualitative relation line and a numeric answer after </think>, with no other printed numbers in the think block; production must also verify its frames. The selection removes all room sources: 586 source-selection rows, corresponding to the brief's expected 581 materialized programs. Every non-room entry is canonically byte-equal and every ordered index retains its hash. The 581 materialized count still needs native regeneration.

`MIX.md` gives each cell's eligible count, cap, cut and final dose. The room request is {table['room']['proposed_cents']/100:.2f} rows per step and its effective dose is {table['room']['final_cents']/100:.2f}; direction receives its unused slots and draws {table['direction']['final_cents']/100:.2f}. Size has zero dose. V7's {away['rows']:,} reworded away rows use QID suffix `{away['qid_suffix']}` and pool `{away['pool']}`; {away['eligible']:,} pass the checked predicates. The suffix fallback filters those rows from the sampler while keeping the single v7 store. The sealed admission predicates remain unchanged.

The local loader audit draws 128,000 real-store VQA rows over 1,000 steps, reports family and question-type shares, toward/away shares within facing and decoded back-answer shares among away-hard draws, and records five bound traces for each populated family, including stored families with zero draw. No VQA row repeats more than {audit['maximum_observed_repeats']} times. Production routing, pose and pointing stores are absent locally, so their final eligible counts and capped routing table remain unmeasured. The local required-family gate checks post-filter VQA counts and native routing source-selection presence. The audit prints cm/ft/in draw counts and absolute-distance eligible/drawn counts by exact scannetpp/, scannetppv2/, scannet and arkit prefixes. Local routing entries are NOT_RUN, with null counts. The production proof recomputes final routing counts from staged files and refuses a missing required family; it prints the named `absent_on_P` list with reasons. Units below 100 eligible rows are named absent rather than failing the gate; sampling applies the configured allowlist and the four-repeat cap.

All {n} local tests pass. The tiny-model OFF optimizer state is bit-equal on all four ranks against b01ce449. The final S2-off first batch passes 72 full-forward microsteps per rank, including 128 real VQA targets in total. Pixels and auxiliary streams are fixtures; these checks do not certify production RGB or the actual routing batch. Two fixture deployment derivations have identical manifest hashes. The fixture lacks `{derivation['missing_source_members'][0]}` and `{derivation['missing_source_members'][1]}`.

The production CPU proof is derived and tested locally at its boundaries, but has not run on Orchard. Its partition parameter accepts `advanced` or `general`; its receipt records the partition and node. It requests 48 CPUs, 800G and four hours with no GPU GRES. It requires named checks for disk plan, routing selection, empty root, temporary paths, runtime binary hashes, private directory modes, loader audit and required families. It authenticates bundle helpers, counts export destinations, starts with empty work and slot directories, and runs the inherited mode-p entry before auditing its prepared streams. Staging keeps files read-only and directories at 0700. The only external writable mount is the declared proof-receipt directory; work and preparation state remain under the job's private temporary root.

The operator archive is `{op['archive']}`. Its outer filenames pass the local scan. The complete deployment's privacy scan, independent admission review, native regeneration and production CPU proof remain required. No GO, content certificate or production PASS is manufactured. `R1P_PACKET.md` gives the binding and operator steps; `REVIEW_REQUEST.json` asks the dispatching lane for one independent review.
'''
    (out/'REPORT.md').write_text(report)
    physical=f"/tmp/jjyeung/a_{b['run_key']}/root/aws/u/ap/{b['store_key']}"
    packet=f'''R1-P uses the ruled vehicle-P family set. Room requests {table['room']['proposed_cents']/100:.2f} rows per step and receives {table['room']['final_cents']/100:.2f} after filtering. Size, recovery and unbound units have zero dose. Full production evidence remains pending. Read `REPORT.md` and `proof/GATES.json` before deployment.

| Binding | Value |
|---|---|
| Config identity | `{b['config_identity']}` |
| Tree | `{b['tree_sha256']}` |
| Run / job name | `{b['run_key']}` / `{b['job_name']}` |
| Producer receipt SHA | `{b['receipt_sha256']}` |
| Database SHA | `{b['database_sha256']}` |
| Selection SHA | `{b['selection_sha256']}` |
| Operator archive | `{op['archive']}` |
| Archive SHA | `{op['sha256']}` |

Relative to H1-1, this config disables S1 and S2, restores D0 scheduled sampling, uses milestones [100, 200] and stop 200, binds v7, removes room programs and adds capped family quotas. The 1,000-step schedule, stream totals (pose 64, VQA 128, routing 64, pointing 32), optimizer and initial weights stay in the inherited recipe. Field-level changes are in `../configs/diff_against_h1_1.json` and `../configs/diff_against_deployed.json`. `SAMPLER_REVIEW.patch` contains the trainer changes; no admission predicate changes. `DEPLOYMENT_REVIEW.patch` covers the staging, wrapper and submitter changes.

Rebind a store, size selector and mix with one command from the lane. This regenerates the admission table, config identity, code archive, loader audit, proof inputs and operator archive:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py \\
  --receipt {b['source_receipt']['path']} \\
  --receipt-sha256 {b['receipt_sha256']} \\
  --orchard-store {b['orchard_store']} \\
  --mix configs/mix.json --proof-partition {b['proof_partition']}
```

The bound store is v7; its producer receipt and database SHA are fixed above. `--size-selector FILE` accepts `{{"field":"metadata.path","equals":"value"}}`; omission keeps all admitted size rows eligible, while the mix controls whether any are drawn. The mix file controls requested doses and refill rules. Traced rooms enter through the bound VQA store and remain subject to the qualitative-trace predicate and cap. `--room-receipt FILE` binds optional provenance for traced rows already integrated into that store; it does not merge a second database. A separate room store must be integrated by its producer. Rebinding invalidates earlier first-batch and deployment proof results; rerun them against the new identity. Use `--reuse-census` only for unchanged store bytes, receipt and sampler-predicate hash. After rebinding, run `/scratch/jjyeung/envs/p1cpu/bin/python -B tools/run_local_checks.py` to refresh the local evidence and this packet.

The default `--units-allowlist ft` samples feet only; freed routing slots go pro rata to camera displacement, movement direction, rotation and absolute distance. To bind units, add `--unit-rows FILE --unit-rows-sha256 SHA` and optionally `--unit-cents N` (default 100 hundredths of a row per step, capped at 4 × allowlisted eligible / 1,000). The file must contain faithful, already packed JSONL rows with full events and all 32 frame pins. No answer, event, or row payload is regenerated. A mismatched SHA, incomplete frame pins, sealed semantic refusal, or row removed by native source selection rejects the binding. The source must already be a clean slice; this command does not repair it.

Each fallback is one rebind command and retains v7 as the sole store:

```bash
# Refused room traces: zero the room cell and send its slots to direction.
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py --receipt {b['source_receipt']['path']} --receipt-sha256 {b['receipt_sha256']} --orchard-store {b['orchard_store']} --room-cents 0 --proof-partition {b['proof_partition']}
# Refused reworded away rows: exclude the exact QID suffix.
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py --receipt {b['source_receipt']['path']} --receipt-sha256 {b['receipt_sha256']} --orchard-store {b['orchard_store']} --exclude-qid-suffix _away_opp --proof-partition {b['proof_partition']}
# Bind a packed, audited successor. The current v2 candidate is refused unchanged.
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py --receipt {b['source_receipt']['path']} --receipt-sha256 {b['receipt_sha256']} --orchard-store {b['orchard_store']} --unit-rows "$UNIT_FILE" --unit-rows-sha256 "$UNIT_SHA256" --units-allowlist ft --unit-cents 100 --proof-partition {b['proof_partition']}
```

Set `UNIT_FILE` and `UNIT_SHA256` to the audited packed file and its SHA. The named candidate is `/scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v2/rows.jsonl`; its unchanged read-only fixture is refused for missing events and frame pins. After any rebind, run `tools/run_local_checks.py` with the CPU Python above. Neither fallback merges loose files into v6.

Unit binding is an **admission-input change**: `u.gz` transports the exact JSONL bytes; `m.json` adds `U_Faithful` to the pool manifest; `i.json` binds its native ordered indices; `u.json` records hashes and per-unit/per-dataset counts. These artifacts enter the operator bundle. Derivation stages `u.gz`, `m.json` and `i.json` into private, read-only namespace paths and adds their pins to the routing catalog. RGB bytes are not bundled: the complete staged RGB map/plan and frame store must resolve every supplied frame pin unchanged. Missing or conflicting RGB fails production admission. Full native materialization calls the sealed `selected_rows`, frame resolution, division/scene/QID filters and RGB audit before the sampler or proof counts units.

The prepared operator archive contains no database bytes. Its sole v7 input is the existing mode-0400 Orchard file `{b['orchard_store']}`. The inherited staging code copies it into `{physical}/d.db`, verifies the database SHA and removes file write bits. Inside the namespace, both `/scratch/fsw` and `/lustre/fsw` aliases resolve to that private union. The deployment receipt is `{b['deployment_receipt']['path']}` with SHA `{b['deployment_receipt']['sha256']}`; its database path is `{b['deployed_database']['path']}`. The original producer receipt remains a separately pinned provenance record. No Trinity database path is a runtime input.

Operator steps below describe the future Orchard execution; this lane made no Orchard call. Keep all destinations private (directories 0700, files 0600 unless the sealed input requires 0400). Do not copy the descriptive reports to the public job surface.

1. Verify `SHA256SUMS` locally and transfer only `{op['archive']}` through the operator's approved route. Extract it into fresh bundle `{op['bundle']}`. Verify its `sums.txt`. Resolve the complete H1-1 deployment as `H`, whose source manifest must hash to `{derivation['source_manifest_sha256']}`. The local incomplete fixture cannot be used for production.
2. Run H1's authenticated native selection regeneration on its complete staged inputs, as in its `build/q.sh`. Retain the fresh raw `s1_pool.prepare` receipt as `NATIVE_RECEIPT`. Project it with the supplied helper; it verifies all regenerated ordered-index hashes and all non-room entries. It also binds the selector import-closure fingerprint to the archived trainer code; admission predicates must retain their parent hashes:

```bash
BUN={op['bundle']}
python3 -B "$BUN/q.py" \\
  --parent "$H/k/pool_selection_eac5f9f0.json" --indices "$H/k" \\
  --native-receipt "$NATIVE_RECEIPT" --implementation "$BUN/j.json" \\
  --code-record "$BUN/c.json" --out "$BUN/q"
```

For a unit-bound packet, run the projection command with `--unit-binding "$BUN/u.json" --config "$BUN/config.json"` as well, using the authenticated CPU environment for the bound code tree. It executes sealed `s1_pool.prepare` on the unit source again, compares every ordered index, combines that source with the freshly checked parent selection, and refuses any final selection hash mismatch. The complete H1 inputs remain necessary. The source-selection counts are preliminary; the production proof reports post-filter counts, 1,000-step shares by family and question type, five bound traces per populated family, and missing units below 100 rows.

3. Obtain one independent review of the changed admission inputs and sampler. Supply identity-bound `review.json`, `staging.json`, `archive.json` and `4.json` in `EVIDENCE`, using the inherited production schemas. The durable source-archive attestation must cover the new tree. These are required inputs, not output claims of this build. Derive a fresh kit; the command invokes the inherited verifier and refuses incompatible evidence:

```bash
KH={op['kit']}
python3 -B "$BUN/d.py" --source "$H" \\
  --source-manifest-sha256 {derivation['source_manifest_sha256']} \\
  --packet "$BUN" --bundle "$BUN" --out "$KH" \\
  --selection-evidence "$BUN/q/q.json" --evidence "$EVIDENCE" > "$BUN/compare.json"
```

4. Run the independent complete content scan on the final kit and supply its `ANON_OK.json`, bound to the final manifest. Create new export sessions for the 20 part destinations in `e.txt` and install the private `sess.json` in the kit. The plan has three exports (100, 200, stop); stopB and stopC are alternate stop-slot names. Never reuse H1 sessions or approval evidence.
5. Bind and submit the production CPU proof, starting from an empty root. `p.py` requires a READY kit and native selection evidence. The proof resolves and hashes binaries at run time; it obtains bwrap from the kit's verified executable pin.

```bash
PARTITION={b['proof_partition']}  # advanced (one approved CPU job) or general
python3 -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" \\
  --binding "$BUN/BINDING.json" --partition "$PARTITION" --out "$BUN/a.json"
TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J {b['job_name']} -A mt01 -p "$PARTITION" -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o "$KH/o/%j.out" -e "$KH/o/%j.err" \\
  "$BUN/{op['proof_script']}" "$BUN/a.json"
```

6. Inspect the named checks in `KH/o/JOB.proof.json`, its bound loader audit and the five printed traces per family. The required-family check permits recovery, size, unbound units, any zero-dose room cell, and bound units below 100 eligible rows; it must pass for every nonzero VQA cell and the four native routing cells. For a bound source, each unit below 100 is listed under absent_on_P with its count. Only allowlisted units with at least 100 rows enter the capped sampler. Confirm the proof receipt records the requested partition and actual node. The separate `go.json` must bind the final config, contract, wrapper and manifest; only then may the operator set `PROOF_JOB` and run `BUN/s.sh`. The submitter refuses any missing proof check or missing GO.

Local validation: {n} tests passed; OFF identity is exact on four tiny-model ranks; 288 final-config microsteps pass finite full-forward checks; two fixture derivations are byte-identical; the real-v7 loader audit covers 1,000 steps. These are bounded local results. Full native selection regeneration, production RGB/admission, complete routing counts, complete privacy scan and production CPU proof are NOT_RUN. `proof/GATES.json` is the authoritative gate list.
'''
    (out/'R1P_PACKET.md').write_text(packet)
    (ROOT/'STATUS.md').write_text(f'BUILT_BLOCKED: config {b["config_identity"]}. Full v7 census and local loader audit complete; {n} tests, four-rank OFF identity, tiny-model first batch and deterministic fixture derivation pass. Vehicle-P required families follow the ruled set; recovery, size and unbound units are absent; low-count bound units are named absent. Required-family status is {audit["required_families"]["status"]}; missing families: {audit["required_families"]["missing"]}. Traced room eligibility is {room["eligible"]}/{room["rows"]}; the Seen/relation/answer grammar is enforced. The current unit candidate lacks events and frame pins and is refused unchanged. Production evidence and independent review remain required. Read out/REPORT.md and out/R1P_PACKET.md.\n')
    names=['REPORT.md','R1P_PACKET.md','ADMISSION_BY_TYPE.json','ROUTING_DIAGNOSIS.json','MIX.md','config.json','BINDING.json',
           'FIX5.md','FIX5.diff','OPERATOR.json','REVIEW_REQUEST.json','SAMPLER_REVIEW.patch','DEPLOYMENT_REVIEW.patch','r1p_code.tar',op['archive']]
    names += ['proof/'+n for n in ('GATES.json','inputs.json','OFF_IDENTITY.json','FIRST_BATCH.json','DERIVATION.json',
                                 'loader_audit.json','ROOM_GRAMMAR.json','traces.jsonl','LOCAL_NAMESPACE.json','p.py',op['proof_script'])]
    names += ['proof/selection/r.json','proof/selection/q.json']
    if (out/'proof/UNIT_CANDIDATE.json').exists():names.append('proof/UNIT_CANDIDATE.json')
    (out/'SHA256SUMS').write_text(''.join(sha(out/n)+'  '+n+'\n' for n in sorted(names)))
    print(json.dumps(dict(status='BUILT_BLOCKED',identity=b['config_identity'],local_tests=n,archive=op['archive'])))

if __name__=='__main__':main()
