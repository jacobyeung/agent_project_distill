"""Describe the pinned packet and the exact remaining operator actions."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parents[1]
def sha(n):return hashlib.sha256((H/n).read_bytes()).hexdigest()
def load(n):return json.loads((H/n).read_text())
ids=load('ids.json');up=load('UPLOAD.json');audit=load('evidence/fix8_admission/config_tests.json')
sbatch='TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap8c74b291 -o "$KH/o/%j.proof.out" -e "$KH/o/%j.proof.err" -A mt01 -p general -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue "$BUN/a_8c74b291.sh"'
hashrows={
 'Selection r.json / payload/d_eac5f9f01587803b.json':sha('payload/d_eac5f9f01587803b.json'),
 'EQUAL q.json / payload/d_e48ab85bb9364aab.json':sha('payload/d_e48ab85bb9364aab.json'),
 'Native implementation digest':'2a4ef06888c59743516f5f7edad4ac3d45c6868cc5d3034ddae13654c8a6cc9c',
 'Config identity':ids['identity'],'Pending-review config key':ids['config_key'],'Admission contract':ids['contract'],
 'Regeneration tool':sha('tools/selection_check.py'),'Executed regeneration script build/q.sh':sha('build/q.sh'),
 'Deriver payload/d.py':sha('payload/d.py'),'Proof build/a_8c74b291.sh':sha('build/a_8c74b291.sh'),
 'Guarded patch build/c_patch.sh':sha('build/c_patch.sh'),'payload/sums.txt':sha('payload/sums.txt'),
 'Upload archive '+up['archive']:up['sha256'],'UPLOAD.json':sha('UPLOAD.json'),
 'orch_h1.sh':sha('orch_h1.sh'),'Unchanged jb.sh':sha('payload/jb.sh'),
 'Unchanged EXPORT_OBJECTS.txt':sha('EXPORT_OBJECTS.txt')}
table='\n'.join('| '+n+' | `'+v+'` |' for n,v in hashrows.items())
report=f'''The H1 packet pins the exact regenerated selection and its EQUAL report. Native validation, authentication and the routing implementation check pass on the final local configuration. Production preparation remains an Orchard prerequisite; this workspace contains no production preparation proof or submission approval.

The selection is the unchanged byte copy of `BUN/q_6c18a2bf/o/r.json` from the reported 03:50Z Orchard run. Its paired report is `o/q.json`; local copies are under `evidence/fix7_selection/orchard_equal_6c18a2bf/o/`. The guard verifies the SHA-pinned report, content, implementation, source tree, executed tool, input inventory and all index checks before deriving. The H1 implementation pin is scoped to H1. No selection field was relabeled or reserialized.

`tests/test_fix8_pin.py` independently rehashes all 12 native index files, compares every raw content field, applies the D0 direct-to-VQA projection and reproduces the new selection. The raw count is 92,607; the projected count is 83,184. Both difference lists are empty. The report records the exact imported dependency versions; the single Devin review of the tool and pin must inspect that report and its native outputs. The user launches that review.

| Binding or artifact | SHA256 / value |
|---|---|
{table}

The run key remains `17c4ffa4`; all 44 export object names remain byte-identical. KH remains `/project/community/jjyeung/okh7/x_3fdda0fb`, and the real persistent root remains `/project/community/jjyeung/okh7/r/39504485`. The trainer archive, code tree, production jb.sh and every derived training-wrapper byte remain unchanged. The selected input and its catalog mapping change the config identity; the admission contract remains unchanged. The local config key `{ids['config_key']}` includes the PENDING review pin. The supplied independent review changes that pin and therefore the final filename; read the definitive key from `compare.json`. Its identity must remain `{ids['identity']}`.

The local source kit is incomplete. The local derivation uses an explicitly recorded fixture-manifest authority and stays FIXTURE; the shipped deriver retains the production source-manifest authority `de6e7e0fac4036889fb4112792fbaa2d6f362a0cde09722ba6e93a6a39e7f32b`. Config, selection and training source bytes are real. Full sealed-source reproduction, READY derivation and certification occur on Orchard. Repeated local derivations produce identical manifests; all packet generators reproduce identical output hashes.

| CPU audit on the final config | Result and scope |
|---|---|
| `carrier_c1_run.validate`, H1 policy, route-policy authentication, native source/archive authentication | PASS |
| `s1_routing.build` implementation conditional | PASS with exact `eac5f9f0…` bytes; zero changed closure members |
| Native `s1_routing.build` through line 219 | Reached the missing r16 receipt with real selection bytes; relocation and model descriptor are isolated fixtures |
| Native synthetic routing through line 456 | PASS; 2 rows; negative blocker, division, count and suffix-budget cases pass |
| Full native `s1_admission.admit` locally | PARTIAL: missing `{audit['results']['admit']['detail'].split('input: ')[-1]}`; no fabricated parent/model/row receipt |
| Remaining preparation | Production streams, legacy DB, models, frame reads, faithful >=95% camera gate, complete seals and first-batch boundary require Orchard |
| Regression suite | test_admission_config and all five fix7 tests PASS; deriver 19 checks; patch 7 cases; gate binding PASS |
| Proof and submission tests | Local proof logic/mount isolation PASS; 13 submission receipt cases PASS; native indices and deterministic rebuild PASS |

The regeneration runtime test deliberately retains the D0 reference configuration because the equality tool compares against that baseline. The admission and routing tests use the final H1 configuration. Exact results and logs are in `evidence/fix8_admission/`; `config_tests.json`, `pin_tests.json`, `proof_tests.json` and `submit_tests.json` identify their retained test directories. The routing limits are recorded in `evidence/fix7_admission/latest.json`.

The production CPU proof is `build/a_8c74b291.sh`, also shipped as `BUN/a_8c74b291.sh`. Its embedded driver checks the certified FINAL KH, manifest, exact config pin, identity, contract, selected bytes, equality report, jb.sh and runtime hashes. It executes jb.sh's exact cold-start prefix through export-session and staging-entry validation, followed by job.sh's certificate check, production import preflight and `g.py p`, then the unchanged `b/r.sh p 0 -> b/i.py -> b/w.py -> s1_admission.admit(prepare_only=True)` path. It never executes the training-mode selector or mode t. The import preflight checks p/t/u dependencies without executing training. The production 3.8 TB node-local free-space guard and actual session-name validation remain in force.

An outer bubblewrap namespace maps a fresh physical `/tmp/jjyeung/p_8c74b291_<job>/tmp/` onto `/tmp`, isolates the persistent root, and isolates KH's arm/run mirrors. The production configuration, logical paths, source bytes and staging functions remain unchanged. The rest of the filesystem is read-only; only proof-local storage and KH/o receive writes. Network access and GPU device nodes are absent in the outer namespace; `CUDA_VISIBLE_DEVICES=''` is forced throughout. No existing jb.sh, job.sh, go.json, production run or persistent slot is edited. The real job automatically reuses **nothing** from this proof: staging, preparation and cold-start claims are isolated, and the real wrapper performs its normal staging and admission again.

After mode p returns, the driver calls native `b/d.effective` against the isolated physical run and validates the prepared source/config/frame seals. It writes `KH/o/<job>.proof.json` with PASS/FAIL, rc, start/end/elapsed timing, full admission result, prepared pins/seals, exact manifest/config/runtime bindings and physical locations. `KH/o/<job>.proof.log`, `.proof.out`, `.proof.err`, `.w.steps`, `.steps` and `.preflight.*.json` retain diagnostics. The native receipt remains at `/tmp/jjyeung/p_8c74b291_<job>/tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4/inputs/data_receipt.json`. PASS means full production preparation and RGB audit reached the first-batch boundary. It does not mean a CPU forward batch or GPU first step ran: native prepare_only returns immediately before `first_batch_check` (`s1_admission.py:277–281`). Catchable failures produce FAIL with rc; a forced kill may leave RUNNING, which never qualifies for submission.

Mode p's native resource contract requests zero GPUs (`b/i.py:26–28`, `b/w.py:32–43`). The exact submission below omits GPU GRES. Four hours allow 1 h 39 min beyond D0's 1 h 51 min preparation plus approximately 30 min staging. Orchard partition policy and production imports were not queried under the local-only scope; no code requirement for a GPU allocation was found. If the scheduler rejects a zero-GPU job, preserve that refusal for the operator; this packet does not silently request a GPU or retry. The local mount test omits only the network namespace because this sandbox denies NETLINK_ROUTE; the shipped script retains it.

The operator sequence is **patch -> o.sh -> g.sh -> review.json -> z.sh derive -> anon/certify -> proof job -> go.json -> s.sh**. These commands are provided for the operator; none ran on Orchard in this task.

1. Deliver `build/c_patch.sh` as `/project/community/jjyeung/okh7/t_c8b460a1.sh` through the authorized opaque transport. Verify SHA256 `{sha('build/c_patch.sh')}`. The patch targets bundle `i_1be16f28` and authenticates the exact retained live starting state in `evidence/fix6_before/payload/`; it refuses another state, occupied target KH/root, linked targets, bad sums and foreign review/staging evidence before mutation. It retains replaced files and obsolete identity-bound evidence in `BUN/v_8`, adds the new selection/report/proof files, and rechecks sums. It preserves the trainer and old KH. A refusal is a stop for operator inspection, never a reason to bypass its guards. `orch_h1.sh` is the reproducible fresh-bundle transport and is not the command for an existing live bundle.

```bash
O=/project/community/jjyeung/okh7
BUN=$O/i_1be16f28
KH=$O/x_3fdda0fb
printf '%s  %s\\n' {sha('build/c_patch.sh')} "$O/t_c8b460a1.sh" | sha256sum -c -
bash "$O/t_c8b460a1.sh"
cd "$BUN"
bash o.sh
PY_GATE=/project/community/jjyeung/latency/envs/fit/bin/python3 BW_GATE=/usr/bin/bwrap bash g.sh
```

2. The user launches one Devin review of the tool and exact selection/report pair plus packet bindings. The operator supplies the resulting PASS `review.json` with this identity, source revision, contract, reviewer and `admission_scope=pinned-template-and-native-data-derivation`. Do not convert the bundled PENDING record into a claimed review. Then derive, inspect `compare.json`, perform the actual content scan, supply CLEAN `anon.json` and certify:

```bash
bash z.sh derive
python3 -m json.tool compare.json
# Supply the actual independently checked CLEAN anon.json for this manifest and its external records.
bash z.sh certify
# Ensure the existing real sess.json contains the 44 unchanged, unused, unexpired export sessions, mode 0600.
PROOF_JOB=$({sbatch})
PROOF_JOB=${{PROOF_JOB%%;*}}
export PROOF_JOB
printf '%s\\n' "$PROOF_JOB"
```

3. After the proof job finishes, inspect `KH/o/$PROOF_JOB.proof.json`. Require PASS, rc 0, PREPARED, effective-config verification and matching final config/manifest/identity/contract/wrapper bindings. A failure stops the sequence. No automatic retry or resubmission is provided.

```bash
python3 -m json.tool "$KH/o/$PROOF_JOB.proof.json"
# Supply separately authorized go.json bound to this final identity, contract, jb.sh SHA and final KH manifest.
bash "$BUN/s.sh"
```

`s.sh` checks the separate GO and `PROOF_JOB` receipt before sbatch. It rejects missing/failed/stale proofs and wrong configuration, manifest, contract, wrapper, CPU visibility or preparation status. The proof itself grants no production GO. No production review, anon certificate or go.json was manufactured locally. All work here used local CPU and workspace files; no SSH, network, Orchard, GPU, Git or deletion command ran.
'''
(H/'REPORT.md').write_text(report)
fix=f'''The H1 selection and SHA-pinned EQUAL report pass the round-7 deriver guard; production preparation is pending on Orchard.
Selection: eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9; exact r.json bytes, never relabeled.
EQUAL report: e48ab85bb9364aab228da7b23033605935e384761f76b0e6527c5e221b1c14b4; raw/final differences [], all 12 native indices verified.
H1 implementation: 2a4ef06888c59743516f5f7edad4ac3d45c6868cc5d3034ddae13654c8a6cc9c; tool: {sha('tools/selection_check.py')}.
Config identity: {ids['identity']}; pending-review key: {ids['config_key']} (read final reviewed key from compare.json).
Contract: {ids['contract']} (unchanged); KH x_3fdda0fb; persistent root r/39504485.
run_key 17c4ffa4, all 44 EXPORT_OBJECTS, trainer/tree and production wrapper bytes remain unchanged.
Final-config audit: native validate/authenticate and s1_routing implementation check PASS with real selection bytes; build reaches missing r16 at line 219 with isolated relocation/model fixtures.
Full native local admit stops on missing production pointing receipt; full production preparation is not claimed locally. Local kit remains FIXTURE.
Tests: test_admission_config + all five fix7 tests PASS; 19 deriver checks, 7 patch cases, gate binding, 12 real indices, deterministic rebuild PASS.
Proof: build/a_8c74b291.sh (also payload); SHA256 {sha('build/a_8c74b291.sh')}.
Proof uses certified FINAL KH, exact production staging/preflight/mode p (prepare_only), CUDA_VISIBLE_DEVICES='', then stops before first batch/mode t.
Proof isolates /tmp, slots and KH mirrors under /tmp/jjyeung/p_8c74b291_<job>; real job reuses nothing; jb.sh/go.json/training wrappers are untouched.
Submit: {sbatch}
Four hours includes 1 h 39 min margin beyond 1 h 51 min mode p + 30 min staging; mode p requires zero GPUs; general availability is unqueried.
Outputs: KH/o/<job>.proof.json (admission, prepared seals, bindings, timing, rc), .proof.log/.out/.err and native step/preflight logs.
Local dry tests: shell success/failure, seal refusal and real filesystem namespace isolation PASS; 13 submission receipt cases PASS. Production proof NOT RUN.
Patch: build/c_patch.sh SHA256 {sha('build/c_patch.sh')}; guarded retained live bundle i_1be16f28 state; backs up to v_8; refusal stops.
Payload sums: {sha('payload/sums.txt')}; upload {up['archive']} SHA256 {up['sha256']}.
Operator order: patch -> o.sh -> g.sh -> review.json -> z.sh derive -> anon/certify -> proof job -> go.json -> s.sh.
The user launches one Devin tool+pin review; review/anon/GO records remain operator-supplied. REPORT.md gives exact commands and bindings.
Set/export PROOF_JOB from sbatch; require PASS/rc=0 plus final config/manifest match; s.sh enforces proof before submission.
Full hashes and audit evidence: evidence/fix8_admission/ and SHA256SUMS.txt. No SSH/network/Orchard/GPU/Git/deletion.
'''
assert len(fix.splitlines())<=25
(H/'FIX8.md').write_text(fix)
(H/'DIFF.md').write_text('''The packet derives H1 from the exact regenerated selection plus its SHA-pinned EQUAL report. The new configuration identity binds unchanged selected content to the real H1 implementation.

- The override adds pool_selection_eac5f9f0.json and selection_equality.json and replaces the stale added catalog mapping. The guard pins the executed selection tool; its report/content/implementation checks remain enforced.
- Conditional authorization and PENDING review/staging records bind the new identity. The run key, export names, trainer, production wrappers and admission contract stay unchanged.
- a_8c74b291.sh executes the certified production preparation path with isolated physical state and emits a sealed-data proof receipt before any training. s.sh requires a passing receipt for the final manifest/config in addition to separate GO.
- The guarded live patch, sums, upload archive, transport and reports carry the new bindings. The patch accepts only its recorded live starting state and retains replaced bytes in v_8.
- Native CPU audits use the final config and unchanged real selection bytes. Local tests cover native index equality, deterministic derivation, preparation-script isolation, failure receipts and submission refusals. Full production preparation and the user-launched Devin review remain pending.

REPORT.md contains full identities, evidence limits and operator commands. FIX8.md is the short operator card. evidence/fix8_patch_manifest.json records patch members; evidence/fix8_admission/delivery.json and SHA256SUMS.txt seal the packet.
''')
print('FIX8 lines',len(fix.splitlines()))
