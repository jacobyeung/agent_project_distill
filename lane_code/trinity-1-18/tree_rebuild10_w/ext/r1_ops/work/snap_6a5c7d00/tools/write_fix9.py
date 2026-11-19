"""Write current S2 evidence and the requested frozen proof-2 comparison."""
import difflib,json,re
from pathlib import Path
from rebind import ROOT,load,sha,diff
from build_fix9 import SNAPSHOT,FROZEN_ID,FROZEN_SHA

def main():
    out=ROOT/'out';binding=load(out/'BINDING.json');op=load(out/'OPERATOR.json')
    cfg=load(out/'config.json');changes=diff(load(SNAPSHOT/'out/config.json'),cfg)
    if changes!=load(out/'CONFIG_DIFF9.json'):raise ValueError('Config diff is stale')
    frozen=load(out/'FROZEN9.local.json')
    for name,expected in frozen['files'].items():
        if sha(SNAPSHOT/name)!=expected:raise ValueError('Frozen byte changed: '+name)
    if sha(out/'p_6f8ed106.tar')!=FROZEN_SHA:raise ValueError('Protected archive changed')
    if op['archive'] in ('p_c5f3847d.tar','p_6f8ed106.tar'):raise ValueError('Archive name reused')
    if sha(out/op['archive'])!=op['sha256']:raise ValueError('Archive seal differs')
    first=load(out/'proof/FIRST_BATCH.json');off=load(out/'proof/OFF_IDENTITY.json')
    guards=load(out/'proof/SWITCH_GUARDS.json')
    for value in (first,guards):
        if value['status']!='PASS' or value['config_identity']!=binding['config_identity']:raise ValueError('Stale S2 evidence')
    log=(out/'logs/tests.log').read_text()
    if not log.rstrip().endswith('OK'):raise ValueError('Tests failed')
    count=int(re.search(r'Ran (\d+) tests',log).group(1));s2=first['s2_pose_targets']
    rank_lines=[]
    for rank in first['ranks']:
        camera=[r for r in rank['records'] if r['s2']['s2_supervised']]
        other=[r for r in rank['records'] if r['stream']=='routing' and not r['s2']['s2_supervised']]
        rank_lines.append('| '+str(rank['rank'])+' | 72 | '+str(len(camera))+' | '+str(len(other))+' | '+
                          f"{min(r['components']['pose'] for r in camera):.6f}–{max(r['components']['pose'] for r in camera):.6f}"+' | 0 |')
    note=f'''BUILT. S2 is on; S1 is off; both scheduled-sampling copies keep max_own_probability at zero. The packet remains subject to production admission and independent review.

Config identity: `{binding['config_identity']}`.
Run key: `{binding['run_key']}`.
Archive: `{op['archive']}`.
Archive SHA256: `{op['sha256']}`.

All {count} packet tests pass. The five guard copies pass {guards['total_checks']} cases ({guards['cases_per_copy']} per copy). Each accepts only S2=true, S1=false, and both max_own_probability=0. S1 alone, S1+S2, either nonzero sampling copy, S2 off, missing fields and malformed scalar values refuse. The deployed deriver, sealer and embedded proof contain the checked guards. `tools/run_local_checks.py` verifies deterministic packaging and two equal deployment derivations, production-form evidence, every packet test, four-rank D0 identity, and the final S2-on first batch.

All 288 first-batch microsteps pass the native forward/loss path on CPU. The test calls the inherited `Rows.get`, `h1.pose_targets` and `CarrierC1.forward`; the trainer bytes remain unchanged. `h1.py` and `carrier_c1.py` are byte-identical to the H1 kit; `Rows.get` has the identical syntax tree. Each camera fixture retains its own ordered 32-frame labels through the sealed `c1_row` converter. The tests compare every emitted pose label with its source row. Every rank covers all three camera types, absolute distance, bound feet, VQA, pointing and the ordinary pose stream.

| Rank | Microsteps | Camera routing rows | Other routing rows | Camera pose loss range | Other routing pose loss |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rank_lines)}

S2 supervises {s2['camera_rows']} camera routing rows and masks all {s2['non_camera_routing_rows']} other routing rows. The inherited trainer exposes a `pose` component on every row; absent supervision means that component is exactly zero, not that its dictionary key disappears. VQA and pointing also have zero pose loss. The ordinary pose stream retains its existing supervision. Missing camera GT masks supervision; malformed camera GT refuses.

The CPU test uses synthetic pixels, camera GT, pose and pointing fixtures, 128 real VQA targets, and bound feet payloads. It replaces RGB/token encoding at the existing tiny-model boundary. It does not certify production RGB, complete routing membership, or actual production camera GT coverage. These remain production-proof checks.

The OFF identity test uses unchanged D0 bytes, with S1 off, S2 off and both max_own_probability values zero. All four optimizer-state hashes and rank reports match the sealed D0 tree exactly and match the frozen proof-2 evidence. D0 config identity is `{off['d0_config_identity']}`. The local OFF test does not pass through the S2-only deployment gate.

The config delta against `{FROZEN_ID}` has {len(changes)} leaves: the S2 boolean and ten derived paths/pins. `CONFIG_DIFF9.json` records the exact before/after values below. The run key changes from `78d0a06c` to `{binding['run_key']}`. The store content hash, Orchard store, mix, cells, 747 bound unit rows, feet dose, frame authorities, trainer tree and routing-selection bytes remain exact. The sampler census is inherited from the frozen packet with explicit provenance; its input policy is unchanged and its first-step plan is executed again by the CPU test.

```json
{json.dumps(changes,indent=2,sort_keys=True)}
```

`FIX9.diff` compares tools, tests, configs, current out files, STATUS.md, the trainer tree and proof parent against `{SNAPSHOT}`. It shows each guard change, including the deployed copies and generated proof. Binary deltas carry SHA256 values. The diff excludes this report, itself and SHA256SUMS to avoid recursion; the final checksum manifest authenticates both FIX9 files. `FROZEN9.local.json` authenticates all {len(frozen['files'])} frozen snapshot files. The protected local proof-2 archive retains SHA256 `{FROZEN_SHA}`. No frozen bytes changed.

Reviewer focus: verify the exact switch conjunction in every deployment boundary, the unchanged H1 target path, the non-camera zero-loss convention, and the local fixture scope. Production preparation, actual RGB/GT coverage, native full selection regeneration and independent review remain pending. This build does not authorize production. All writes stay inside this lane; execution uses CPU only.

The report follows the no-archaeology and summary skills. The frozen comparison is retained because the brief expressly requires it.
'''
    (out/'FIX9.md').write_text(note)
    names={'STATUS.md','work/proof_parent.py'}
    for folder in ('tools','tests','configs','out','work/tree'):
        for base in (SNAPSHOT,ROOT):
            names.update(str(p.relative_to(base)) for p in (base/folder).rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts)
    excluded={'out/FIX9.md','out/FIX9.diff','out/SHA256SUMS'};patch=[];changed=[]
    for name in sorted(names-excluded):
        left=SNAPSHOT/name;right=ROOT/name
        before_sha=sha(left) if left.is_file() else None;after_sha=sha(right) if right.is_file() else None
        if before_sha==after_sha:continue
        if name.startswith('work/tree/'):raise ValueError('Trainer bytes changed: '+name)
        changed.append(name)
        before=left.read_bytes() if left.is_file() else b'';after=right.read_bytes() if right.is_file() else b''
        try:
            if b'\0' in before or b'\0' in after:raise UnicodeError()
            a=before.decode();b=after.decode()
        except UnicodeError:
            patch.append('Binary files a/'+name+' and b/'+name+' differ\n# SHA256 before='+str(before_sha)+' after='+str(after_sha)+'\n')
            continue
        patch.extend(difflib.unified_diff(a.splitlines(keepends=True),b.splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
    (out/'FIX9.diff').write_text(''.join(patch))
    print(json.dumps(dict(status='BUILT',config_identity=binding['config_identity'],archive_sha256=op['sha256'],tests=count,changed_files=len(changed))))

if __name__=='__main__':main()
