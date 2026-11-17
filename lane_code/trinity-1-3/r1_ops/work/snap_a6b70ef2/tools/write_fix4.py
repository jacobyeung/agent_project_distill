"""Build the requested frozen-snapshot delta without Git."""
import difflib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_841f0637')
WHY={
 'tools/make_proof.py':'Call temporary_paths after command construction; require directory_modes; run the loader audit through stdin so argv remains opaque.',
 'tools/package_operator.py':'Require the same eight named receipt checks in the submitter.',
 'tools/unit_binding.py':'Reject unpacked unit inputs with an explicit missing-events/frame-pins error; never regenerate their payload.',
 'tools/rebind.py':'Bind v7; parameterize room dose, away-QID exclusion, feet allowlist and unit dose; cap allowlisted units and redistribute routing pro rata; isolate fixture outputs; compare both config diffs against deployed H1-1.',
 'tools/admission_census.py':'Count traced-room sealed checks and qualitative eligibility separately, and identify the exact reworded-away marker during the full store census.',
 'tools/selection_check.py':'Allow the sampler-only vehicle_p module in the authenticated selector import closure; preserve all sealed admission predicates.',
 'work/tree/student_pilot/type_mix.py':'Apply the unit allowlist and 100-row threshold to sampler populations; filter the configured away-QID suffix; retain the four-repeat cap.',
 'work/tree/student_pilot/vehicle_p.py':'List unbound units and low-count bound units under absent_on_P; keep required-family failures for actual required populations.',
 'work/tree/student_pilot/loader_audit.py':'Audit the exact filtered populations and report total unit counts separately from feet sampling eligibility.',
 'tests/test_packet.py':'Exercise the generated proof main() receipt, v7 census and cap, unit allowlist and named absences, the real read-only unit candidate refusal, deployed config baseline, and fallback filters.',
 'tools/finalize.py':'Publish current v7 counts, blockers, complete fallback and unit rebind commands, proof scope and FIX4 checksums.',
 'tools/run_local_checks.py':'Generate the FIX4 snapshot delta and current packet after tests pass.',
 'tools/write_fix4.py':'Generate the file/what/why inventory and unified delta against snap_841f0637.',
 'configs/mix.json':'Request room 1.72 and size zero; send freed VQA slots to direction; default units to feet only and zero while unbound.',
 'configs/diff_against_h1_1.json':'Use the deployed H1-1 baseline, byte-identical to diff_against_deployed.json.',
 'configs/diff_against_deployed.json':'Bind the current config and sampler policy against deployed H1-1.',
 'configs/r1p.json':'Bind the current tree, v7 receipt, selection and mix identity.',
}
def main():
    patches=[];changed=[]
    for folder in ('tools','tests','configs','work/tree'):
        left=SNAPSHOT/folder;right=ROOT/folder
        paths={p.relative_to(left) for p in left.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        paths|={p.relative_to(right) for p in right.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        for rel in sorted(paths):
            a=left/rel;b=right/rel
            before=a.read_bytes() if a.is_file() else b'';after=b.read_bytes() if b.is_file() else b''
            if before==after:continue
            name=folder+'/'+str(rel);changed.append(name)
            patches.extend(difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
    for name in ('SAMPLER_REVIEW.patch','DEPLOYMENT_REVIEW.patch'):
        a=SNAPSHOT/'out'/name;b=ROOT/'out'/name
        before=a.read_text() if a.exists() else '';after=b.read_text()
        if before!=after:
            changed.append('out/'+name)
            patches.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/out/'+name,tofile='b/out/'+name))
    out=ROOT/'out';(out/'FIX4.diff').write_text(''.join(patches))
    b=json.loads((out/'BINDING.json').read_text());op=json.loads((out/'OPERATOR.json').read_text());c=json.loads((out/'ADMISSION_BY_TYPE.json').read_text())
    lines=[f"Fix 4 delta against `{SNAPSHOT}`.", '',f"Config identity: `{b['config_identity']}`. Archive: `{op['archive']}`. SHA256: `{op['sha256']}`.",'',
        f"The full v7 census checks {c['vqa_rows']:,} rows. Traced room counts: {json.dumps(c['traced_room'],sort_keys=True)}. Reworded away counts and markers: {json.dumps(c['reworded_away'],sort_keys=True)}.",'',
        'The room cell requests 1.72 rows per step. The current literal Locate/Relate/Estimate predicate rejects the v7 Seen/relation/numeric-answer traces; eligible room count is zero and the required-family gate fails. No predicate change or room-zero fallback is silently approved. R1P_PACKET.md documents both one-command fallbacks.', '',
        'No unit source is bound. The read-only v2 candidate has 1,224 rows (ft 1,130; in 94; cm 0), but lacks top-level events and frame pins; the real rebind command refuses its unchanged fixture copy. Successful packed-source native binding/regeneration and feet-only population/cap behavior are separate fixtures. The default unit request is 1.00 row per step, capped at 4 × allowlisted eligible / 1,000; freed routing slots go pro rata to the four native program cells.', '',
        'The proof main() fixture writes a receipt with all eight evaluated checks: disk_plan, routing_selection, empty_root, temporary_paths, runtime_binaries, directory_modes, loader_audit and required_families. Its fixture admission/runtime boundaries do not certify Orchard production preparation.', '',
        'File / change / reason:', '']
    for name in changed:lines.append('- `'+name+'`: '+WHY.get(name,'Refresh the review patch against its declared baseline.') )
    lines+=['','Generated outputs: out/BINDING.json, config.json, records/, ADMISSION_BY_TYPE.json, MIX.md, proof inputs and audits, operator archive, OPERATOR.json, REPORT.md, R1P_PACKET.md, proof/GATES.json, SHA256SUMS and STATUS.md bind the current v7 identity and keep production blocked. All command output and test results remain in out/logs/.', '',
        'No Git, SSH, Orchard, GPU, deletion or write outside this lane was used. The requested FIX4 comparison is the only historical narrative added; packet prose describes current state.', '']
    (out/'FIX4.md').write_text('\n'.join(lines))
    print(json.dumps({'changed_files':changed,'diff':'out/FIX4.diff'}))
if __name__=='__main__':main()
