"""Write both reviewable config diffs and current packet evidence."""
import difflib,json,re,shutil
from pathlib import Path
from rebind import ROOT,load,sha,write,diff

def packet_diff(base,snapshot,destination):
    names=set()
    for folder in ('tools','tests','configs','out/records','out/operator','out/proof','out/units'):
        for source in (base,snapshot):
            names.update(str(p.relative_to(source)) for p in (source/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    names.update('out/'+n for n in ('config.json','BINDING.json','OPERATOR.json','ADMISSION_BY_TYPE.json','CONFIG_DIFF10.json','FIX10_CELLS.json','FIX10_BUILD.json','FIX10_PHASES.json','FIX10_OFFENDERS.json','FIX10_VARIANT.json','FIX10_UNIT_REMOVE_CHECK.json','FIX10_PROTECTED_ARCHIVES.json','MIX.md','REPORT.md','R1P_PACKET.md','REVIEW_REQUEST.json'))
    patches=[];changed=[]
    for name in sorted(names):
        left=snapshot/name;right=base/name
        if not right.is_file():continue # Historical outputs are not part of this fresh packet.
        before=left.read_bytes() if left.is_file() else b'';after=right.read_bytes()
        if before==after:continue
        changed.append(name)
        try:
            if b'\0' in before+after:raise UnicodeError()
            a=before.decode();b=after.decode()
            patches.extend(difflib.unified_diff(a.splitlines(keepends=True),b.splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
        except UnicodeError:
            patches.append(f'Binary files a/{name} and b/{name} differ\n# SHA256 before={sha(left) if left.is_file() else None} after={sha(right)}\n')
    destination.write_text(''.join(patches));return changed

def main():
    out=ROOT/'out';roots={'A':ROOT,'B':ROOT/'work/fix10b'};packets={}
    for letter,base in roots.items():
        b=load(base/'out/BINDING.json');op=load(base/'out/OPERATOR.json');v=load(base/'out/FIX10_VARIANT.json')
        snapshot=Path(v['snapshot']);cfg=load(base/'out/config.json')
        assert diff(load(snapshot/'out/config.json'),cfg)==load(base/'out/CONFIG_DIFF10.json')
        assert sha(base/'out'/op['archive'])==op['sha256']
        if letter=='B':
            target=out/op['archive']
            if target.exists():assert sha(target)==op['sha256']
            else:
                with target.open('xb') as f:f.write((base/'out'/op['archive']).read_bytes())
        log=(base/'out/logs/tests.log').read_text();assert log.rstrip().endswith('OK'),letter
        count=int(re.search(r'Ran (\d+) tests',log).group(1))
        changed=packet_diff(base,snapshot,out/('FIX10'+letter+'.diff'))
        packets[letter]=dict(config_identity=b['config_identity'],run_key=b['run_key'],archive=op['archive'],sha256=op['sha256'],
            S2=cfg['h1']['routing_pose_targets'],tests=count,packet_root=str(base),snapshot=str(snapshot),changed_files=changed,config_diff=load(base/'out/CONFIG_DIFF10.json'))
    a_cfg=load(roots['A']/'out/config.json');b_cfg=load(roots['B']/'out/config.json')
    assert a_cfg['type_mix']==b_cfg['type_mix']
    assert a_cfg['remove_files'][:-1]==b_cfg['remove_files'][:-1]
    assert a_cfg['remove_files'][-1]['sha256']==b_cfg['remove_files'][-1]['sha256']
    a_audit=load(roots['A']/'out/proof/loader_audit.json');b_audit=load(roots['B']/'out/proof/loader_audit.json')
    assert a_audit['tables']==b_audit['tables'] and a_audit['first_step']==b_audit['first_step']
    write(out/'FIX10_IDENTITIES.json',packets)
    offenders=load(out/'FIX10_OFFENDERS.json');cells=load(out/'FIX10_CELLS.json');build=load(out/'FIX10_BUILD.json');phases=load(out/'FIX10_PHASES.json')
    lines=['BUILT FOR REVIEW; production admission remains blocked by missing local RGB and source streams. Both packets remove exactly 601 out-of-division VQA rows through one appended pinned REMOVE list. The sealed trainer and its admission predicates, store, division, and inherited filter files retain their bytes.','',
        '| Packet | S2 | Config identity | Run key | Archive | Archive SHA256 |','|---|---|---|---|---|---|']
    for letter,p in packets.items():lines.append(f"| {letter} | {p['S2']} | `{p['config_identity']}` | `{p['run_key']}` | `{p['archive']}` | `{p['sha256']}` |")
    lines+=['','The new list is `records/n.json`, SHA256 `'+sha(out/'records/n.json')+'`. Its opaque deployment name follows the existing extra-file staging path: each bundle contains the list, its manifest pins the bytes, the deriver stages it read-only at the new packet path, and the config appends that exact pin to `remove_files`. The file uses the sealed one-`row_key`-per-line format. `FIX10_OFFENDERS.json` records every QID, type, pool, and dataset/scene after both exclusions and all six inherited lists. No duplicate QIDs remain.','',
        '| Pool and question type | Removed |','|---|---:|']
    lines += [f'| {k} | {v} |' for k,v in offenders['by_pool_type'].items()]
    lines += ['','The full census contains 204,413 rows and admits 203,812. The 173 removed counting questions split into 71 counting-cell rows and 102 totals-cell rows. All affected populations and cells follow; ceilings use floor(4 × eligible / 1000 × 1000) / 1000, and sampler cells use the hundredths floor.','',
        '| Family | Old eligible | New eligible | Old cell | New cell | New ceiling |','|---|---:|---:|---:|---:|---:|']
    lines += [f"| {r['family']} | {r['old_eligible']} | {r['eligible']} | {r['old_cents']/100:.2f} | {r['cents']/100:.2f} | {r['ceiling_milli']/1000:.3f} |" for r in cells if r['changed']]
    lines += ['','Room uses 1.70 at 425 eligible rows. The sealed ordered refill assigns its two-cent reduction to direction, giving 31.19. VQA remains 128.00 per step. Routing requests remain displacement 18.25, movement direction 15.88, rotation 12.53, absolute distance 16.34, feet 1.00, recovery 0; full production routing populations remain unmeasured. Native unit regeneration retains 747 rows (683 feet and 64 inches), with only feet sampled. `FIX10_UNIT_REMOVE_CHECK.json` verifies that the new list matches none of those 747 rows.','',
        'The unmodified full-store VQA call fails locally before reaching the division violation because a pinned RGB file is absent: `'+build['native_unmodified']['error']+'`. This is a local-data limitation, not a production PASS. The supplementary full-store structural regression executes the sealed build with only `common.binding` RGB-byte reads mocked. It raises the exact reported ValueError without the list and builds '+str(build['with']['count'])+' rows with it. Every output QID and scene is checked. The test does not read or certify RGB bytes.','',
        '| Production prepare entry point | Local result |','|---|---|']
    lines += [f"| {name} | {v['status']}: `{v.get('error','')}` |" for name,v in phases['phases'].items()]
    lines += ['','Local validation reaches native unit regeneration, the full VQA row census, native capped sampler preparation, the 1,000-step/128,000-draw loader audit, and four-rank first-batch forward/loss checks. All '+str(packets['A']['tests'])+' tests and `tools/run_local_checks.py` pass for A and B. Each run checks deterministic packaging, two equal fixture deployments, production-form evidence validation, wrong-evidence refusal, and exact D0 optimizer states. First batches use real selected VQA targets with synthetic pixels and auxiliary-stream fixtures. A supervises camera routing poses; B masks every routing pose. The deployment helpers enforce S2=true for A and S2=false for B; both require S1=false and zero own-sampling probability in both schedule copies. No Slurm or Orchard call occurred.','',
        'Reviewer checks: verify the REMOVE list against the pinned division and v7 bytes; inspect the 601-row scope, staging pin, room cap and refill; confirm A requires S2 on and B requires S2 off; run complete production preparation with RGB, pointing, pose/model metadata and routing archives. Inspect actual routing populations/caps and first-batch labels there. Independent review and production CPU proof remain required.','',
        '`FIX10A.diff` compares current packet tools, tests, configs and evidence against `snap_8246a4dd`; `FIX10B.diff` compares the fallback against `snap_2c67f1f2`. Binary deltas carry SHA256 values. Historical reports/archives absent from the fresh fallback workspace are not treated as deletions. Trainer inventory equality is tested. Existing root archives and frozen snapshot files were not modified. The exact config diffs below are the required reviewer comparisons; retaining them follows the explicit brief.']
    for letter,p in packets.items():lines+=['',f'Packet {letter}: exact config diff.','','```json',json.dumps(p['config_diff'],indent=2,sort_keys=True),'```']
    (out/'FIX10.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'STATUS.md').write_text('Both packets are built and locally validated. A '+packets['A']['config_identity']+'; B '+packets['B']['config_identity']+'. Each removes 601 out-of-division rows; room=1.70 and direction=31.19. Full production admission remains unverified because RGB, pointing, pose/model metadata and complete routing inputs are absent locally. Read out/FIX10.md, FIX10A.diff and FIX10B.diff.\n')
    for letter,base in roots.items():
        target=base/'out'
        archives={packets[letter]['archive'],'r1p_code.tar'}
        if letter=='A':archives.add(packets['B']['archive'])
        files=[p for folder in ('proof','records','units','logs') for p in (target/folder).rglob('*') if p.is_file()]
        files += [p for p in target.iterdir() if p.is_file() and p.name!='SHA256SUMS' and (p.suffix!='.tar' or p.name in archives)]
        (target/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(target))+'\n' for p in sorted(set(files))))
    print(json.dumps({k:{n:v[n] for n in ('config_identity','run_key','archive','sha256','tests')} for k,v in packets.items()},indent=2))
if __name__=='__main__':main()
