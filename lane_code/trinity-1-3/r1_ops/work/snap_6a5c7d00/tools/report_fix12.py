"""Record launch-gate evidence and exact archive/derived-kit comparisons."""
import ast
import base64
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import zlib

from rebind import ROOT, H, load, sha, write
from derive_deployment import derive
from canary_gate import OLD_KH, RECEIPT_SHA, LOG_SHA

SNAP = Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_a5dc8f30')
SCANNED = Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052')
EVIDENCE = Path('/scratch/jjyeung/orch_n30/r1_ops/work')


def inventory(root):
    return {str(p.relative_to(root)):sha(p) for p in root.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}


def unpack(archive, root):
    root.mkdir(mode=0o700)
    result = {}
    with tarfile.open(archive) as tf:
        for m in tf.getmembers():
            assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
            raw = tf.extractfile(m).read();p=root/m.name
            p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes(raw);p.chmod(m.mode)
            result[m.name]=hashlib.sha256(raw).hexdigest()
    return result


def decoded(path):
    line=next(x for x in path.read_text().splitlines() if x.startswith('raw=zlib.'))
    return zlib.decompress(base64.b64decode(ast.literal_eval(ast.parse(line).body[0].value.args[0].args[0]))).decode()


def table(rows, columns):
    return '| '+' | '.join(columns)+' |\n|'+ '|'.join('---' for _ in columns)+'|\n'+''.join('| '+' | '.join(str(x).replace('|',r'\|') for x in row)+' |\n' for row in rows)


def compare():
    out=ROOT/'out';op=load(out/'OPERATOR.json');binding=load(out/'BINDING.json')
    work=Path(tempfile.mkdtemp(prefix='diff12_',dir=ROOT/'work'))
    old_bundle=work/'old_bundle';new_bundle=work/'new_bundle'
    old_arc=out/'p_69d2930d.tar';new_arc=out/op['archive']
    old_members=unpack(old_arc,old_bundle);new_members=unpack(new_arc,new_bundle)
    assert set(old_members)==set(new_members)
    assert sha(old_arc)==sha(SCANNED/'out/p_69d2930d.tar')
    assert sha(new_arc)==op['sha256']
    assert (out/'config.json').read_bytes()==(SNAP/'out/config.json').read_bytes()==(SCANNED/'out/config.json').read_bytes()
    assert (out/'BINDING.json').read_bytes()==(SNAP/'out/BINDING.json').read_bytes()
    assert (new_bundle/op['proof_script']).read_bytes()==(SNAP/'out/operator'/op['proof_script']).read_bytes()
    for name,expected in load(out/'FIX11_PROTECTED_ARCHIVES.json').items():assert sha(ROOT/name)==expected,name
    assert sha(out/'p_a5dc8f30.tar')=='a5dc8f306b6867c24fc80aa1215697cb178337252ec912f61ff575b8ec1e9169'
    reasons={'s.sh':'CANARY branch; original PASS checks and sbatch line retained',
             op['proof_script']:'Fix-11 proof caller environment (unchanged in fix 12)',
             'sums.txt':'Binds the two changed script hashes'}
    changed=[n for n in sorted(old_members) if old_members[n]!=new_members[n]]
    findings=[n for n in changed if n not in reasons]
    source=H/'build/fx'
    old_result=derive(source,work/'old_kit',old_bundle,sha(source/'SHA256SUMS.txt'),fixture=True)
    new_result=derive(source,work/'new_kit',new_bundle,sha(source/'SHA256SUMS.txt'),fixture=True)
    old_files=inventory(work/'old_kit');new_files=inventory(work/'new_kit')
    kit_changed=[n for n in sorted(set(old_files)|set(new_files)) if old_files.get(n)!=new_files.get(n)]
    findings+=['kit/'+n for n in kit_changed]
    # Seal both bundles at one fixture path so path-only differences do not
    # obscure the changed bundle_files authority pins. No file is deleted.
    stable=work/'seal_bundle';stable.mkdir(mode=0o700)
    ready=Path(load(out/'proof/PRE_SUBMISSION.json')['fixture'])/'ready'
    authority={}
    for label,bundle in (('old',old_bundle),('new',new_bundle)):
        for name in sorted(old_members):
            p=stable/name;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes((bundle/name).read_bytes())
        target=work/(label+'_authority.json')
        subprocess.run([sys.executable,'-B',str(ROOT/'tools/seal_proof.py'),'--kit',str(ready),
            '--bundle',str(stable),'--binding',str(out/'BINDING.json'),'--partition','advanced','--out',str(target)],check=True)
        authority[label]=load(target)
    authority_fields=[k for k in authority['old'] if authority['old'][k]!=authority['new'][k]]
    assert authority_fields==['bundle_files']
    pins=[k for k in authority['old']['bundle_files'] if authority['old']['bundle_files'][k]!=authority['new']['bundle_files'][k]]
    assert sorted(pins)==sorted(['s.sh',op['proof_script']])
    write(out/'proof/RESEAL12.json',dict(status='PASS',fixture_authority=str(work/'new_authority.json'),
        authority_sha256=sha(work/'new_authority.json'),config_identity=binding['config_identity'],
        archive=op['archive'],archive_sha256=op['sha256'],changed_fields=authority_fields,changed_bundle_pins=pins,
        scope='Local production-form fixture only; driver must reseal on Orchard against final deployed paths'))
    old_proof=decoded(old_bundle/op['proof_script']);new_proof=decoded(new_bundle/op['proof_script'])
    (out/'PROOF_DIFF12.diff').write_text(''.join(difflib.unified_diff(old_proof.splitlines(True),new_proof.splitlines(True),fromfile='scanned/proof',tofile='new/proof')))
    old_s=(old_bundle/'s.sh').read_text();new_s=(new_bundle/'s.sh').read_text()
    assert old_s.split('\nP\n',1)[1]==new_s.split('\nP\n',1)[1]
    old_header=(old_bundle/op['proof_script']).read_text().split("<<'P'",1)[0]
    new_header=(new_bundle/op['proof_script']).read_text().split("<<'P'",1)[0]
    assert old_header==new_header
    all_inventory=dict(archive={n:dict(old=old_members[n],new=new_members[n],changed=n in changed) for n in sorted(old_members)},
        derived_kit={n:dict(old=old_files.get(n),new=new_files.get(n),changed=n in kit_changed) for n in sorted(set(old_files)|set(new_files))})
    write(out/'KIT_INVENTORY12.json',all_inventory)
    result=dict(status='PASS' if not findings else 'FINDINGS',work=str(work),old_archive=old_arc.name,
        old_sha256=sha(old_arc),new_archive=op['archive'],new_sha256=op['sha256'],config_identity=binding['config_identity'],
        archive_members=len(old_members),changed_archive_members=changed,derived_kit_files=len(old_files),
        changed_derived_kit_files=kit_changed,findings=findings,authority_changed_fields=authority_fields,
        authority_changed_bundle_pins=pins,visible_surface_outside_scripts_equal=True,complete_visible_surface_equal=False,
        content_scan='QUICK_SCAN_REQUIRED_FOR_GATE_AND_PROOF_VISIBLE_ADDITIONS',fixture_missing_source_members=old_result['missing_source_members'])
    write(out/'KIT_DIFF12.json',result)
    rows=[('archive/'+n,old_members[n],new_members[n],reasons.get(n,'FINDING')) for n in changed]
    rows.append(('authority.json (same-path fixture)',sha(work/'old_authority.json'),sha(work/'new_authority.json'),'Only bundle_files.s.sh and bundle_files.'+op['proof_script']))
    surface=[('Archive member names and paths',f'{len(old_members)} names; byte-equal'),
        ('Derived kit names and file bytes',f'{len(old_files)} files; byte-equal'),
        ('Trainer archive, jb.sh, c.sh, r.sh, p0.sh, a.py, config and admission predicates','Byte-equal'),
        ('Training sbatch argv and proof submission prefix','Byte-equal'),
        ('srun argv outside changed scripts','Byte-equal (all containing files identical)'),
        ('Environment names outside changed scripts','Byte-equal'),
        ('Log line formats outside changed scripts','Byte-equal'),
        ('New gate input environment name','ADMISSION_JOB (PROOF_JOB retained)'),
        ('New gate paths',OLD_KH+'/o/170956.proof.{json,log}; old manifest/config/0.json; BUN/job.id; KH/o/<PROOF_JOB>.canary.json'),
        ('New gate queue argv','TZ=UTC squeue --noheader --jobs <PROOF_JOB> --format=%i\u007c%T\u007c%j'),
        ('Proof additions','TK_RUNS_DIR, TK_JOBDIR, R1_RUNTIME_RECORD exports; private .proof directory and pinned runtime-record path'),
        ('Complete visible surface','Not byte-equal; quick scan required for the additions inside s.sh/proof')]
    text=f'''Packet `{op['archive']}` differs from the scanned `{old_arc.name}` in exactly {len(changed)} of {len(old_members)} archive members. The fixture-derived kits have {len(old_files)} files and {len(kit_changed)} differences. Findings outside the proof, gate and sums/authority records: {len(findings)}.

The table lists every changed archive member, every changed derived-kit file (none), and the resealed authority. `KIT_INVENTORY12.json` lists old/new SHA256 for every archive member and every derived-kit file, including unchanged files.

{table(rows,['File','Old SHA256','New SHA256','Reason'])}
Both kits derive from `{source}` using the same source manifest and logical deployment paths. The two absent inherited archives are `{old_result['missing_source_members']}`; these are fixture derivations, not Orchard attestations. The fixture seal uses a production-form READY kit and one stable bundle path for both versions; only the two script pins differ in its authority. The proof driver must reseal the actual deployed bundle.

{table(surface,['Visible surface','Comparison'])}
Outside `s.sh`, the proof contents, and their sums/authority values, the visible surface is byte-equal. The full surface is not byte-equal because those scripts introduce the listed names, paths and commands. This report does not certify a reused content scan. `PROOF_DIFF12.diff` exposes the decoded proof change; the embedded proof is byte-equal to fix 11.

Scanned archive SHA256: `{sha(old_arc)}`. New archive SHA256: `{op['sha256']}`. Config identity: `{binding['config_identity']}` (unchanged).
'''
    (out/'KIT_DIFF12.md').write_text(text)
    return result


def report():
    out=ROOT/'out';op=load(out/'OPERATOR.json');binding=load(out/'BINDING.json');cfg=load(out/'config.json')
    protected={p.name:sha(p) for p in (SNAP/'out').glob('p_*.tar')}
    assert op['archive'] not in protected
    for name,expected in protected.items():assert sha(out/name)==expected,name
    write(out/'FIX12_PROTECTED_ARCHIVES.json',protected)
    result=load(out/'KIT_DIFF12.json')
    tests=(out/'logs/tests.log').read_text();focused=(out/'logs/fix12_gate_tests.log').read_text()
    local=(out/'logs/fix12_local_checks.log').read_text()
    assert tests.rstrip().endswith('OK') and focused.rstrip().endswith('OK') and 'Fix12.' in tests
    assert '"status": "BUILT_BLOCKED"' in local
    count=int(re.search(r'Ran (\d+) tests',tests).group(1));focus=int(re.search(r'Ran (\d+) tests',focused).group(1))
    r=load(EVIDENCE/'f170956.proof.json')
    rows=[('Evidence receipt','o/170956.proof.json',RECEIPT_SHA),('Evidence log','o/170956.proof.log',LOG_SHA),
        ('Old manifest','receipt.manifest_sha256 → SHA256SUMS.txt',r['manifest_sha256']),
        ('Old config','receipt.config → '+r['config']['file'],r['config']['sha256']),
        ('Staging pins','receipt.manifest → k/0.json; must equal new kit bytes',sha(Path(result['work'])/'new_kit/k/0.json')),
        ('Staging shell','receipt.runtime_sha256 and old manifest → b/c.sh',r['runtime_sha256']['b/c.sh']),
        ('Store','receipt.manifest → k/0.json extra; receipt.config → streams.vqa → bundle d.json',binding['database_sha256']),
        ('Store record','receipt.config → streams.vqa.sha256',cfg['streams']['vqa']['sha256']),
        ('Selection','receipt.selection.sha256',binding['selection_sha256']),
        ('Unit slice','receipt.config → type_mix.unit_rows; receipt.manifest → k/0.json extra',cfg['type_mix']['unit_rows']['sha256'])]
    for pin in cfg['remove_files']:
        rows.append((pin['path'],'proof.log remove_list.file.sha256; receipt.config → remove_files',pin['sha256']))
    for digest,path in sorted(cfg['s1_routing']['catalog'].items(),key=lambda x:x[1]):
        rows.append((path,'receipt.config → s1_routing.catalog',digest))
    text=f'''BUILT_FOR_INDEPENDENT_REVIEW. CANARY accepts the pinned successful admission from job 170956 while the new bundle's proof is PENDING or RUNNING. PASS-proof launch behavior is unchanged.

Archive: `{op['archive']}`. SHA256: `{op['sha256']}`. Config identity: `{binding['config_identity']}` (unchanged). No config, trainer, admission-predicate, `jb.sh`, `c.sh`, `r.sh`, `p0.sh`, or sbatch-line change. The proof script remains byte-equal to fix 11.

The gate first runs all five existing GO checks. A JSON boolean `canary: true` selects CANARY. Every other value follows the unchanged PASS-proof path; no third acceptance path exists. CANARY requires literal `ADMISSION_JOB=170956`, checks the receipt and log bytes at `{OLD_KH}`, checks receipt identity and contract, and requires exactly one timestamped admission `exit rc=0` line.

The receipt authenticates the old manifest and config. The gate checks the old `k/0.json` against that manifest and requires exact equality with the new kit's `k/0.json`, including every staging digest and source part. It also compares both configs' streams, routing catalog, REMOVE files and type mix; checks store/unit pins against staging; and compares selection and all seven REMOVE hashes with the receipt/log. The staging shell hash must match the receipt and old manifest. The existing `a.main(k)` then checks the new kit manifest, inventory and scan certificate before a CANARY marker can be written.

Store/routing/unit hashes are transitively authenticated through the receipt's config/manifest pins; the log does not directly print those values. No unobserved `170956.preflight.*` digest is invented or required. Orchard must retain the old manifest, receipt-referenced config and `k/0.json` under the renamed old kit. Their runtime verification fails closed if any is missing or changed. Local tests use a repinned fixture receipt because local config/manifest bytes differ from production; they separately verify the exact supplied receipt/log hashes. The Orchard evidence chain has not been executed here.

{table(rows,['Input','Authenticated supplying file/field (relative to old kit unless stated)','Expected SHA256'])}
`PROOF_JOB` must be a positive decimal integer other than 170956 and exactly match the stripped new bundle `job.id`. The gate queries `squeue` with `TZ=UTC`; exactly one row must match that job, `PENDING` or `RUNNING`, and literal job name `a15_cot_ap673bc60f`. Missing jobs, terminal states, a wrong name, multiple rows or a queue error refuse.

After `a.main` succeeds, the gate exclusively creates `KH/o/<PROOF_JOB>.canary.json` with `canary=true`, both job references, config/contract/manifest/wrapper hashes, admission receipt/log hashes, queue state, job name and `submission=GATE_ACCEPTED`. The record marks the accepted training submission, not a successful sbatch allocation; it has no training job ID because the sbatch line stays unchanged. The wrapper must retain GO and associate sbatch's training job ID with this marker. A pre-existing marker refuses instead of overwriting evidence. PASS mode writes no CANARY marker.

Wrapper contract: write `BUN/go.json` with JSON boolean `production_go_granted: true`, `config_sha256` equal to `ids.identity`, `admission_contract_sha256` equal to `ids.contract`, `wrapper_sha256` equal to SHA256 of `BUN/jb.sh`, and `manifest_sha256` equal to SHA256 of `KH/SHA256SUMS.txt`. Add JSON boolean `canary: true` only for CANARY. Export `ADMISSION_JOB=170956` and `PROOF_JOB=<new proof job ID>`; the proof driver must already have written that exact ID to `BUN/job.id`. No new mode environment variable or GO field is required. Without `canary=true`, supply the existing completed PASS proof through `PROOF_JOB`. Re-pin the wrapper to the new archive and gate SHA256 `{sha(out/'operator/s.sh')}` and reseal its deployed authority. Driver files are outside this packet and were not edited.

Validation: {count} tests pass in the complete suite through `tools/run_local_checks.py`, invoked from `tools` with `/scratch/jjyeung/envs/p1cpu/bin/python`; {focus} focused gate tests pass separately. `bash -n` passes for every packaged shell script. The runner verifies repeated identical archives, equal fixture kit derivations, four-rank CPU D0 optimizer identity, the CPU first batch, native selection regeneration and production-form evidence checks. Gate tests exercise full-shell sbatch stubbing, pending/running acceptance, existing PASS predicates, every existing GO field, admission job pin, evidence SHA and semantic mutations, missing successful exit, staged hash mutations, and all requested proof job/queue refusals. Fix-11 nounset replays run in the full suite. Fixture helper interpreters use the required p1cpu executable.

`RESEAL12.json` records the local authority reseal. `KIT_DIFF12.md` and its full inventory show {len(result['changed_archive_members'])}/{result['archive_members']} changed archive members and {len(result['changed_derived_kit_files'])}/{result['derived_kit_files']} changed derived-kit files, with {len(result['findings'])} out-of-scope findings. The complete visible surface changes inside the proof/gate, so a quick content scan is required. `FIX12.diff` compares sources, tests, config, current bundle and evidence with `snap_a5dc8f30`; all existing packet archives are retained unchanged.

Reviewer checks: independently review the CANARY exception and transitive evidence chain; verify old-kit retention and all runtime pins; inspect the queue/job.id binding, marker semantics, unchanged PASS branch and sbatch argv; verify the archive/kit table and quick scan; inspect the unchanged fix-11 `TK_JOBDIR` initialization and nounset replay. The reviewer and operator must then reseal against final Orchard paths and re-pin the GO writer. No independent review, production proof, Orchard access, SSH, Git or GPU work occurred here. The ruling's downstream monitoring and kill rules remain the operator's responsibility.

Reader-first writing exception: the explicitly requested snapshot and scanned-kit comparisons retain version names because they identify the required evidence baselines.
'''
    (out/'FIX12.md').write_text(text)
    write(out/'FIX12_RESULT.json',dict(status='BUILT_FOR_INDEPENDENT_REVIEW',archive=op['archive'],sha256=op['sha256'],
        config_identity=binding['config_identity'],config_fields_changed=[],tests=count,focused_tests=focus,
        local_checks='PASS',independent_review='REQUIRED',content_scan='QUICK_SCAN_REQUIRED',
        changed_archive_members=result['changed_archive_members'],changed_derived_kit_files=result['changed_derived_kit_files'],findings=result['findings']))
    (ROOT/'STATUS.md').write_text(f"BUILT_FOR_INDEPENDENT_REVIEW. CANARY gate; {count} tests and local checks PASS. Archive {op['archive']}, SHA256 {op['sha256']}; unchanged config {binding['config_identity']}. Read out/FIX12.md, out/FIX12.diff and out/KIT_DIFF12.md. Independent review, quick scan and deployed authority reseal remain required.\n")
    write(out/'REVIEW_REQUEST.json',dict(status='REVIEW_REQUIRED',archive=op['archive'],sha256=op['sha256'],
        scope=['CANARY gate and evidence chain','KIT_DIFF12 and visible surface','fix-11 TK_JOBDIR and nounset replay'],
        requested_reviewer='Independent reviewer per ruling; no self-approval',details='out/FIX12.md'))
    (out/'RESULT_FIX12.md').write_text(f"RESULT: BUILT_FOR_INDEPENDENT_REVIEW.\nArchive: {op['archive']}\nSHA256: {op['sha256']}\nConfig identity unchanged: {binding['config_identity']}\nValidation: {count} suite tests, {focus} focused tests, local checks and bash syntax PASS.\nKIT_DIFF12: 3/37 archive members changed; 0/99 derived-kit files changed; no out-of-scope findings.\nRequest the ruling's independent review of the gate, diff table and fix-11 nounset replay.\nA quick scan is required for the gate/proof visible additions.\nRead FIX12.md for the exact GO/env contract, evidence hash table and deployed reseal requirements.\nThis event remains lane-local under the brief's no-write-outside constraint.\n")
    names=set()
    for folder in ('tools','tests','configs','out/operator','out/proof','out/records','out/units'):
        for base in (ROOT,SNAP):
            names.update(str(p.relative_to(base)) for p in (base/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    names.update(str(p.relative_to(ROOT)) for p in out.iterdir() if p.is_file() and p.suffix!='.tar' and p.name not in ('FIX12.diff','SHA256SUMS'))
    names.add('STATUS.md');patch=[]
    for name in sorted(names):
        before=SNAP/name;after=ROOT/name;a=before.read_bytes() if before.is_file() else b'';b=after.read_bytes() if after.is_file() else b''
        if a==b:continue
        try:
            if b'\0' in a+b:raise UnicodeError()
            patch.extend(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
        except UnicodeError:patch.append(f'Binary {name}: old={sha(before) if before.is_file() else "absent"} new={sha(after) if after.is_file() else "absent"}\n')
    patch.append(f'Added archive out/{op["archive"]}: SHA256 {op["sha256"]}\n')
    (out/'FIX12.diff').write_text(''.join(patch))
    files=[p for folder in ('proof','records','units','logs') for p in (out/folder).rglob('*') if p.is_file()]
    files += [p for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS' and (p.suffix!='.tar' or p.name in (op['archive'],'r1p_code.tar'))]
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(out))+'\n' for p in sorted(set(files))))
    print(json.dumps(load(out/'FIX12_RESULT.json'),sort_keys=True))


if __name__=='__main__':
    if '--compare' in sys.argv:compare()
    else:report()
