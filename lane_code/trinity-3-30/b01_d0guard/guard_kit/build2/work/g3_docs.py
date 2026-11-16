"""Record the current release scope and operator-supplied CPU fixture evidence."""
from pathlib import Path
import difflib,sys
B=Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit'
sys.path.insert(0,str(K))
from guard_core import read,write,sha

evidence='out/rehearsal/whole/31f44f39c63b4d68be53660ff5780980/RESULT.json'
operator=dict(status='PASS',scope='Whole-worker CPU fixture only',source='Operator report in the G3 task',
    result=evidence,result_read_by_g3=False,protected_directory_accessed_by_g3=False,
    steps=['stage','prepare','proof','canary','native_subset','merge','admit','publish','fetch','report'],
    proof=dict(passed=20,total=20,token_generation='Pinned historical-token stand-in; no real token identity claim'),
    report=dict(items=20,returncode=3,expected='Refuse incomplete fixture denominator'),
    real_tensors_validated=False,gpu_parity_validated=False,token_identity_validated=False,
    torchvision=dict(overlay='/scratch/jjyeung/orch_n30/b01_d0guard/work/tvoverlay3',version='0.26.0+cpu',
        wheel='work/whl/torchvision-0.26.0+cpu-cp312-cp312-manylinux_2_28_x86_64.whl',
        wheel_sha256='cf547dc0975eb40bc3249be4ccbeb736597d2c3ece305b1c4e5b7a5dd7363567',
        wheel_sha256_source='Operator-supplied; wheel was not read by G3'),
    not_proven=['Real tensor restoration','GPU parity','Token identity','Production cloud staging and allocation'])
write(O/'rehearsal/OPERATOR_EVIDENCE_G3.json',operator)
blockers=read(O/'RELEASE_BLOCKERS.json')
for blocker in blockers['blockers']:
    if blocker['id']=='naming':
        blocker['operator_context']='The seven names sit inside the sealed trainer tree b01ce449, the same tree job 170056 and D0\'s training job already staged on Orchard; ORCH decides.'
        blocker['context_evidence']=['out/NAMING_CONFLICT.json','G3 task: operator-supplied Orchard staging context']
    elif blocker['id']=='whole_worker':
        blocker.update(status='CLOSED',scope='CPU fixture only',evidence=evidence,
            description='The operator reports that the CPU fixture passes stage, prepare, proof, canary, native subset, merge, admit, publish, fetch and report. The report correctly refuses the incomplete fixture. This closes the CPU-fixture blocker only.',
            evidence_source='Operator-supplied; G3 did not access the protected run directory.',
            limitations=['The fixture cannot establish real tensors, GPU parity or token identity.',
                        'Production cloud staging and allocation remain unvalidated.'],
            details='out/rehearsal/OPERATOR_EVIDENCE_G3.json')
blockers['g1_blocker_status']['2']='IMPLEMENTED_AND_CPU_FIXTURE_TESTED; production runtime remains unvalidated'
blockers['g1_blocker_status']['4']='CLOSED_FOR_CPU_FIXTURE; operator-supplied pass; real tensors/GPU parity/token identity unproven'
blockers['not_checked']=[('Production whole-worker execution with real tensors' if item=='Whole-worker execution' else item) for item in blockers['not_checked']]
assert blockers['production_packet_authorized'] is False and blockers['status']=='NOT_READY'
write(O/'RELEASE_BLOCKERS.json',blockers)

source=(K/'admission.py').read_text();original=(K/'admission.g2_orig.py').read_text()
baseline=read(B/'work/G3_BASELINE.json')
assert sha(K/'admission.g2_orig.py')==baseline['code_manifest']['members']['admission.py']['sha256']
(O/'G3_ADMISSION.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),source.splitlines(True),fromfile='G2/admission.py',tofile='G3/admission.py')))
patch=(O/'DIFF.patch').read_text();end=patch.index('--- G1/checkpoint.py')
(O/'DIFF.patch').write_text(''.join(difflib.unified_diff([],source.splitlines(True),fromfile='G1/admission.py',tofile='G3/admission.py'))+patch[end:])
doc=(O/'DIFF.md').read_text().replace('| G2 lines |','| Current lines |')
doc=doc.replace('| `out/guard_kit/admission.py` | 1–64 | insert | Native-only journal merge, request/score/geometry admission; item 2 |',
    '| `out/guard_kit/admission.py` | 1–76 | insert | Native-only journal merge, request/score/geometry admission; item 2 |\n'
    '| `out/guard_kit/admission.py` | 14–27 | canonical JSON comparison | Compare per-key digests after the existing non-answer score normalization; refuse differing content and continue with journal rows; G3 item 1 |\n'
    '| `out/guard_kit/admission.py` | 18–26 | mismatch diagnostics | Write differing keys and fields to `MERGE_DIFF.json`; distinguish an absent field from JSON null; G3 item 1 |')
intro='''
The admission-specific patch against the sealed G2 source is `G3_ADMISSION.patch`. Canonical JSON treats tuples and lists with the same contents equally, while preserving differences such as boolean versus integer values. The existing non-answer score-zeroing policy still applies before comparison. Key cardinality, membership, full-denominator, parity, request binding, score and geometry checks remain enforced. The accepted rows come from the JSON journal.

`out/tests/test_g2.py` exercises tuple/list admission, a changed-score refusal with `MERGE_DIFF.json`, missing/foreign/duplicate keys, absent-versus-null diagnostics, boolean/integer differences and downstream parity/denominator checks (`G2_TESTS.json`).

`work/family.py`, `work/seal.py --g3` and `work/finish.py --g3` refresh and verify the original production member inventory. `G3_SEAL.json` verifies that only `admission.py` differs inside the code tar. Rehearsal files and `.g2_orig.py` backups remain excluded. The operator's mount splitting, torchvision overlay and positional-argument forwarding remain rehearsal-only (`rehearsal/RUNBOOK.md`).
'''
if 'The admission-specific patch' not in doc:doc=doc.replace('\n| File |',intro+'\n| File |',1)
(O/'DIFF.md').write_text(doc)

# Keep the shifted admission citation accurate without rewriting unrelated pin rows.
pin_json=(O/'PIN_CLASSIFICATION.json').read_text()
pin_json=pin_json.replace('"enforcement": "out/guard_kit/admission.py:48"','"enforcement": "out/guard_kit/admission.py:60"')
(O/'PIN_CLASSIFICATION.json').write_text(pin_json)
pin_doc=(O/'PIN_CLASSIFICATION.md').read_text().replace('out/guard_kit/admission.py:48','out/guard_kit/admission.py:60')
pin_doc=pin_doc.replace('| ADAPTER_IMPLEMENTED; WHOLE_WORKER_UNEXECUTED |','| CPU_FIXTURE_OPERATOR_PASS; REAL_TENSORS_UNCHECKED |')
(O/'PIN_CLASSIFICATION.md').write_text(pin_doc)
pin_json=(O/'PIN_CLASSIFICATION.json').read_text().replace('"status": "ADAPTER_IMPLEMENTED; WHOLE_WORKER_UNEXECUTED"','"status": "CPU_FIXTURE_OPERATOR_PASS; REAL_TENSORS_UNCHECKED"')
(O/'PIN_CLASSIFICATION.json').write_text(pin_json)

(O/'rehearsal/RUNBOOK.md').write_text('''# Whole-worker CPU rehearsal

The operator reports a passing CPU fixture at `out/rehearsal/whole/31f44f39c63b4d68be53660ff5780980/RESULT.json`. It covers stage, prepare, proof, canary, native_subset, merge, admit, publish, fetch and report. The proof passes 20/20 comparisons; the unchanged report refuses the 20-item fixture with return code 3, as designed (same `RESULT.json`; `OPERATOR_EVIDENCE_G3.json`). G3 records this supplied evidence without reading or modifying `out/rehearsal/whole/` and does not rerun the namespace worker.

Run this command outside the Codex sandbox on the same compute node:

```sh
/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/rehearsal/run_whole_worker.sh
```

The launcher uses `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, `nice -n 10`, and one thread per numerical library. It creates a fresh operator run under `out/rehearsal/whole/`. A namespace failure stops the command; it does not retry.

`run_whole_worker.py:split_mounts` supports bwrap 0.4.0 by splitting directory binds into `--dir` and per-child binds along later mount paths. This lets bwrap create nested mountpoints without writing inside a read-only bind. This adapter stays outside the production code tar (`../CODE_MANIFEST.json`).

`inside_whole.py` explicitly prepends `/scratch/jjyeung/orch_n30/b01_d0guard/work/tvoverlay3` to `sys.path`. The p1cpu environment lacks torchvision, which the Qwen3VL video processor needs. The operator supplied torchvision `0.26.0+cpu` from `/scratch/jjyeung/orch_n30/b01_d0guard/work/whl/torchvision-0.26.0+cpu-cp312-cp312-manylinux_2_28_x86_64.whl`, SHA256 `cf547dc0975eb40bc3249be4ccbeb736597d2c3ece305b1c4e5b7a5dd7363567` (`OPERATOR_EVIDENCE_G3.json`). G3 did not read or install that wheel. The proof `generate` stand-in accepts and forwards `*args`, including the caller's fifth positional argument. These changes stay outside the production code tar.

The command shares the production phase coordinator (`../guard_kit/worker.py:coordinate`). It stages tiny local exports, invokes the unchanged checker, starts separate checkpoint processes, publishes proof and canary receipts with local readback, reads the candidate subset, merges and admits it, archives and fetches the return, and invokes the unchanged report. Production merge compares canonical JSON digests and then uses journal rows; differing content refuses with `MERGE_DIFF.json` (`../guard_kit/admission.py`, `../G2_TESTS.json`).

The fixture cannot establish real tensor restoration, GPU parity or token identity. Each tiny artifact re-derives only `heads.sha256` and `full_weights.sha256`; other artifact fields retain the supplied metadata values. Model boundaries bypass actual tensor loading, so retained trained-group fingerprints do not validate tiny tensors. The proof substitutes pinned historical tokens. The configuration projections and boundary declarations belong to each operator run's `PREPARATION.json` and phase `BOUNDARY.json` files. Shared pre-staged assets and allocation boundaries also prevent a claim that a full production packet was tested with transport alone changed.

The candidate subset preserves the sealed canary and fills from the proof list in accepted order (`inside_whole.py`). The report's incomplete-read refusal is expected; no unexecuted items are filled. The separate full recorded-row fixture at `records_pass/RESULT.json` has no model decode.

Run the proof-mismatch variant outside the sandbox:

```sh
/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/rehearsal/run_whole_worker.sh --mismatch
```

A valid mismatch publishes a failed `PROOF.json` and creates no candidate canary or arm. The supplied whole-worker pass does not establish this variant. Namespace-free mismatch evidence remains at `records_mismatch/RESULT.json`; process failure and receipt-ordering tests are indexed in `../PROCESS_TESTS.json`.

Inspect the run's `RESULT.json`, phase logs, `PROOF.json`, `CANARY.json`, `IN_JOB_ADMISSION.json` and publication readbacks. The CPU-fixture blocker is closed; real runtime validation and production authority remain required (`../RELEASE_BLOCKERS.json`).
''')
decisions=O/'DECISIONS.md';text=decisions.read_text()
addition='''
- G3 seal inventory: enumerate the live code directory or retain the sealed production member list. Default: retain the sealed list and verify that only `admission.py` changes; operator backups and rehearsal code stay excluded (`out/G3_SEAL.json`).
- G3 evidence boundary: reopen the operator's run directory or record the supplied result. Default: use the operator's CPU-fixture report and leave `out/rehearsal/whole/` untouched; real tensors, GPU parity and token identity remain unproven (`out/rehearsal/OPERATOR_EVIDENCE_G3.json`).
'''
if 'G3 seal inventory:' not in text:decisions.write_text(text+addition)
(B/'STATUS.md').write_text('G3 is in progress: merge regressions and packet tests pass; remaining suites and mutants are running.\nThe production archive has been resealed with the original member inventory (out/G3_SEAL.json).\nThe CPU-fixture blocker is CLOSED on operator-supplied evidence; out/rehearsal/whole/ remains untouched.\nNaming and production authority remain blocked (out/RELEASE_BLOCKERS.json).\nFinal integrity audit and hash index remain to be completed.\n')
print('Release blockers, operator runbook and source differences updated.')
