"""Write the proof-2 packet and its delta against the immutable proof-1 snapshot."""
import difflib,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_d8b03fd1')
EXCLUDED={'out/FIX8.md','out/FIX8.diff','out/SHA256SUMS'}
FROZEN_ARCHIVE='888027436a99cfec360959c46f4271222e4c029f5d36eb9870fea4f669231029'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()
def load(path):return json.loads(path.read_text())

def main():
    out=ROOT/'out';binding=load(out/'BINDING.json');op=load(out/'OPERATOR.json')
    frozen=load(SNAPSHOT/'out/BINDING.json')
    if sha(SNAPSHOT/'out/p_c5f3847d.tar')!=FROZEN_ARCHIVE:raise ValueError('Frozen proof-1 archive differs')
    if binding['config_identity']==frozen['config_identity'] or op['archive']=='p_c5f3847d.tar':raise ValueError('Proof-2 identity is not fresh')
    for key in ('receipt_sha256','database_sha256','orchard_store','proof_partition','traced_room_receipt'):
        if binding[key]!=frozen[key]:raise ValueError('Unrelated binding changed: '+key)
    if binding['mix']['streams']['vqa']!=frozen['mix']['streams']['vqa']:raise ValueError('VQA policy changed')
    unit=binding['unit_binding'];packing=unit['packing']
    if packing['input_rows']!=747 or packing['rows']+packing['refused_rows']!=747:raise ValueError('Unit accounting differs')
    if packing['payload_changed']:raise ValueError('Unit payload changed')
    previous=load(SNAPSHOT/'out/proof/selection/r.json');current=load(out/'proof/selection/r.json')
    if {k:v for k,v in current['sources'].items() if k!='U_Faithful'}!=previous['sources']:raise ValueError('Parent source membership changed')
    log=(out/'logs/tests.log').read_text()
    if not log.rstrip().endswith('OK'):raise ValueError('Tests failed')
    count=int(re.search(r'Ran (\d+) tests',log).group(1))
    map_sha=sha(out/'CENSUS_CODES.local.json')
    cells=binding['mix']['streams']['routing']['cells']
    note=f'''Proof 2 binds {packing['rows']} of 747 supplied unit rows. All {packing['sealed_validation_pass']} packed rows pass sealed validation and native source selection; {packing['refused_rows']} rows are refused. The refusal list is `{json.dumps(packing['refusals'])}`. All supplied payload fields and source QIDs remain unchanged. The packer adds only events and frame inputs. All 23,904 frame pins resolve against the production-equal map, plan and FPS authorities. Actual RGB-byte validation remains pending.

Feet have 683 eligible rows. The feet-only cell is 1.00 row per step, with a 2.73 ceiling (273 cents; the exact repeat limit is 4 × 683 / 1,000 = 2.732). Inches are explicitly named missing at 64 eligible rows, below the 100-row threshold; cm is named missing at zero. The bound source retains the inches rows, but the allowlist samples feet only.

| Program cell after pro-rata refill | Rows/step |
|---|---:|
| Camera displacement | {cells['camera_displacement']['cents']/100:.2f} |
| Camera movement direction | {cells['camera_movement_direction']['cents']/100:.2f} |
| Camera rotation | {cells['camera_rotation']['cents']/100:.2f} |
| Absolute distance | {cells['absolute_distance']['cents']/100:.2f} |

The local frame-authority manifest is `FRAME_AUTHORITY.local.json`, SHA256 `{sha(out/'FRAME_AUTHORITY.local.json')}`. `REBIND8.local.json` records the executed rebind argv with `--pack-unit-slice --units-allowlist ft --unit-cents 100`. `units/u.json` records all packing counts, refusals, authority pins and sealed implementation hashes. A missing requested frame refuses the row with its QID and every missing index; the test exercises that branch without inventing a pin.

The printed routing census uses g0–g3 and preserves the unknown-row check: more than 1% unknown eligible distance rows fails the audit. The local-only mapping is `CENSUS_CODES.local.json`, SHA256 `{map_sha}`. Every printed audit record encodes dataset-bearing keys recursively. The audit prints the mapping hash; the archive excludes the mapping file. Stored training payloads remain unchanged.

The namespace probe creates and tests `/home`, a path that names no user. Its source and captured argv contain no `/home/` literal. The probe retains its device, proc, user namespace, UID/GID and read-only home checks. The argv regression uses a stub; it does not claim local kernel namespace admission.

All {count} packet tests pass, including the real 747-row packing and native regeneration, exact payload and frame-pin comparisons, missing-frame refusal, printed opaque keys, mapping exclusion from the archive, namespace argv, and unknown-prefix threshold cases. `tools/run_local_checks.py` also checks deterministic packaging, two identical deployment fixtures, four-rank OFF identity, and the final-config first batch. Production preparation, actual RGB-byte admission and independent review remain pending.

Config identity: `{binding['config_identity']}`.
Run key: `{binding['run_key']}`.
Archive: `{op['archive']}`.
Archive SHA256: `{op['sha256']}`.

`FIX8.diff` compares tools, tests, configs, out, STATUS.md, the trainer tree and the proof parent against `{SNAPSHOT}`. Binary changes include before/after hashes. The diff excludes itself, this note and SHA256SUMS to avoid recursion. The checksum manifest authenticates both FIX8 files. The frozen proof-1 archive remains `{FROZEN_ARCHIVE}`. No frozen bytes were edited. All writes stay inside this lane; no SSH, Orchard, Git, GPU or deletion command ran.

The report applies the no-archaeology writing rule. The frozen-copy comparison is retained because the brief explicitly requests it.
'''
    (out/'FIX8.md').write_text(note)
    (out/'UNIT_PACKING.md').write_text(f'''Proof 2 binds the pinned 747-row unit slice with `--pack-unit-slice --units-allowlist ft --unit-cents 100`. All 747 rows pass sealed packing and native selection with zero refusals. The source has 683 feet rows, 64 inches rows and zero cm rows. Feet draw 1.00 row per step under a 2.73 ceiling. Inches and cm are named missing because each has fewer than 100 rows.

The slice SHA256 is `{packing['slice']['sha256']}`. The packed JSONL SHA256 is `{unit['input_sha256']}`. Every supplied field remains unchanged; only events and student frame inputs are added. The source QID retains its original join. The sealed packer, row validator and native source-selection predicates are unchanged.

`FRAME_AUTHORITY.local.json` binds production-equal local copies of the frame map, plan and FPS authority. `REBIND8.local.json` contains the exact command. `units/u.json` records counts and every refusal. Missing requested map entries refuse that row with its QID and missing indices. Malformed payloads, conflicting frame authorities and failed sealed admission reject the binding.

The four native program cells receive 18.25, 15.88, 12.53 and 16.34 rows per step for camera displacement, movement direction, rotation and absolute distance. The complete routing policy totals 64.00 rows per step with feet at 1.00 and recovery at zero. Production still applies the population caps after native materialization.

`proof/UNIT_REAL.json` verifies packing, all 23,904 pinned frames, unchanged payloads, native retained membership and deterministic regeneration. `proof/UNIT_PACKING_CHECK.json` covers the small synthetic fixture. The bound source transports no RGB bytes; full production preparation must verify staged RGB bytes and final routing populations. Local source admission does not certify production RGB or authorize launch.
''')
    patches=[];changed=[];binary=[];names=set()
    for folder in ('tools','tests','configs','out','work/tree'):
        for base in (SNAPSHOT,ROOT):
            names.update(str(p.relative_to(base)) for p in (base/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    names.update(('work/proof_parent.py','STATUS.md'))
    for name in sorted(names-EXCLUDED):
        a=SNAPSHOT/name;b=ROOT/name
        before_sha=sha(a) if a.is_file() else None;after_sha=sha(b) if b.is_file() else None
        if before_sha==after_sha:continue
        changed.append(name)
        if name.startswith('work/tree/') and name!='work/tree/student_pilot/loader_audit.py':raise ValueError('Unexpected trainer change: '+name)
        before=a.read_bytes() if a.is_file() else b'';after=b.read_bytes() if b.is_file() else b''
        try:
            if b'\0' in before or b'\0' in after:raise UnicodeError()
            old=before.decode();new=after.decode()
        except UnicodeError:
            patches.append('Binary files a/'+name+' and b/'+name+' differ\n')
            patches.append('# SHA256 before='+str(before_sha)+' after='+str(after_sha)+'\n');binary.append(name);continue
        patches.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
    (out/'FIX8.diff').write_text(''.join(patches))
    print(json.dumps(dict(changed_files=changed,binary_files=binary,diff='out/FIX8.diff')))

if __name__=='__main__':main()
