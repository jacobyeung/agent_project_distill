"""Write exact archive inventories, source diffs, and offline identity evidence."""
import difflib
import hashlib
import json
from pathlib import Path
import sys
import tarfile

OUT=Path(__file__).resolve().parent; ROOT=OUT.parent
sys.path.insert(0,str(OUT/'src'))
from orchard_h10.common import canonical,read_config,sha
from h1eval.cli import code_hash
from h1eval.h10.parity_adapter import reader_code_hash


def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def members(path):
    with tarfile.open(path) as t:return {m.name:t.extractfile(m).read() for m in t if m.isfile()}


a=members(ROOT/'in/prod_pkg/0.tgz');b=members(OUT/'package/0.tgz')
rows=[]
for name in sorted(a.keys()|b.keys()):
    rows.append(dict(path=name,production=digest(a[name]) if name in a else None,
                     package=digest(b[name]) if name in b else None,changed=a.get(name)!=b.get(name)))
write(OUT/'FILE_SHA256_DIFF.json',rows)
(OUT/'FILE_SHA256_DIFF.tsv').write_text('path\tproduction_sha256\tpackage_sha256\tchanged\n'+''.join(
    f"{r['path']}\t{r['production'] or '-'}\t{r['package'] or '-'}\t{str(r['changed']).lower()}\n" for r in rows))
changed=[r['path'] for r in rows if r['changed']]
reasons={
 'orchard_h10/export_pins.py':'Authenticate the pin file, validate its schema, and compare export paths, full hashes, and exact byte counts before staging.',
 'orchard_h10/job.py':'Use the fixed logical archive destination, replace only export constants with pin-file admission, authenticate the pin file before staging, and pass its contents to preparation and its job-local copy to workers.',
 'orchard_h10/operator.py':'Load the new pin module in the sealed standalone helper and authenticate a/export.json at check and submit.',
 'orchard_h10/build.py':'Keep the logical root independent of the new package token; describe the export reference in INPUTS.example.json and the local token inventory.',
 'orchard_h10/prepare.py':'Stage authenticated preparation metadata, pass the selected files to restore, and use the selected config in reader settings. The sealed 544 fallback matches hashes and sizes exactly.',
 'orchard_h10/runner.py':'Pass the authenticated export pin copy to each worker.',
 'h1eval/h10/launch.py':'Read lineage and step from the job-local pin file and carry them unchanged into journal bindings; require the pin-file argument.',
 'b/parity_kit/stage_restore.py':'Select and authenticate preparation files from the pins, preserve their original binding paths, and retain every existing structural guard. The restore description names the selected export.',
 '8.py':'Generated copy of orchard_h10/operator.py; same reason as that source.',
 '9.json':'Generated plan: new package token and hashes/sizes for the explicitly changed sources; the logical root and all other configuration remain fixed.'}
assert set(changed)==set(reasons),changed
full=[];sections=[]
for name in changed:
    before=a.get(name,b'').decode().splitlines(keepends=True);after=b[name].decode().splitlines(keepends=True)
    diff=''.join(difflib.unified_diff(before,after,fromfile='production/'+name,tofile='package/'+name))
    full.append(diff)
    sections.append(f"### `{name}`\n\n{reasons[name]}\n\n")
    if name=='9.json':
        old=json.loads(a[name]);new=json.loads(b[name]);delta=[]
        def walk(x,y,path):
            if isinstance(x,dict) and isinstance(y,dict):
                for k in sorted(x.keys()|y.keys()):walk(x.get(k),y.get(k),path+'/'+k)
            elif x!=y:delta.append(dict(pointer=path,production=x,package=y))
        walk(old,new,'')
        write(OUT/'PLAN_DIFF.json',delta)
        sections.append('Both files contain one generated JSON line. Line 1 changes exactly these JSON fields; `package.patch` includes the complete literal line.\n\n```json\n'+json.dumps(delta,indent=2)+'\n```\n\n')
    else:sections.append('```diff\n'+diff+'\n```\n\n')
(OUT/'package.patch').write_text('\n'.join(full))
public=[];public_sections=[]
public_reasons={'0.tgz':'Sealed payload contains the changes above.',
 '0.json':'New token, payload digest/bytes, and plan digest.',
 'CONFIG.json':'New public token, payload digest/bytes, and plan digest.',
 'BATCH.sh':'Embedded numeric bootstrap descriptor and private-root token use the new package.',
 'PACKAGE.json':'New token and hashes of the generated package files.',
 'INPUTS.example.json':'Adds the required external export-pin reference.',
 '3.py':'Standalone loader remains byte-identical.', 'SUBMIT.cmd':'Submission wrapper remains byte-identical.'}
for name,reason in public_reasons.items():
    old=(ROOT/'in/prod_pkg'/name).read_bytes();new=(OUT/'package'/name).read_bytes()
    status='changed' if old!=new else 'identical'
    public_sections.append(f'- `{name}`: {status}. {reason}\n')
    if old!=new and name!='0.tgz':
        diff=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),
                                        fromfile='production-public/'+name,tofile='package-public/'+name))
        public.append(diff)
        ranges=[line for line in diff.splitlines() if line.startswith('@@')]
        public_sections.append('  Changed line ranges: '+', '.join('`'+r+'`' for r in ranges)+'.\n')
(OUT/'public.patch').write_text('\n'.join(public))
comparison=OUT/'SOURCE_COMPARISON.md'
if not comparison.exists():comparison.write_bytes((OUT/'DIFF.md').read_bytes())
(OUT/'DIFF.md').write_text(
 '# Package diff against production 0.tgz\n\n'
 'Production SHA256: `446a432306b8e68ebfa32228071259a61ffd2ec0dada3ec43a664ba342ca540e`. '
 f'The archive inventory contains {len(a)} production files and {len(b)} package files; '
 f'{len(rows)-len(changed)} files match byte for byte. Nine existing files change and one is added.\n\n'
 '`FILE_SHA256_DIFF.tsv` and `.json` list every member with both full hashes. '
 '`package.patch` contains every changed payload line; the readable diffs below include source line numbers and reasons. '
 '`PLAN_DIFF.json` expands the generated plan line into its exact changed fields.\n\n'
 'All scorers, statistics, items, perturbations, call-cap code, reader/e2e code, tree, heads, '
 'authentication rows, and vendored runtime/environment/dependency inventories are byte-identical. '
 'Only h1eval/h10/launch.py changes within h1eval; only stage_restore.py changes within parity_kit. '
 'No reader source was repinned.\n\n'+''.join(sections)+
 '### Public package files\n\n'+''.join(public_sections)+
 '\n`public.patch` contains every changed public text line, including the full encoded bootstrap line. '
 'The binary payload is covered by the complete member comparison above.\n\n'
 '### Build and operator files outside the payload\n\n'
 '`build_package.py` calls the production builder with local source locations; `audit_package.py` writes this audit. '
 '`fill_export.py` creates operator pins and the small preparation archive. `node_check.py` runs production staging/restore and invokes the supplied, byte-identical `submerge.py`. '
 '`export_544.json`, `export_TEMPLATE.json`, `inputs_544.json`, and `EXPORT_SCHEMA.md` define the input contract. '
 '`tests/test_package.py` tests the new package; `tests/test_constraints.py` retains the production audit and checks only the production extraction. '
 'The latter changes one line from its supplied version, removing src from the unchanged-extraction loop because src now contains the implementation. '
 'The complete new helper/test files are additions with no production counterpart. `REPORT.md` and `OPERATIONS_DELTA.md` describe this package. '
 'The original report is preserved verbatim as `REPORT_R1.md`.\n\n'
 '### Supplied builder and stager comparison\n\n'
 '`KIT_COMPARISON.json` inventories the supplied builder snapshot against production. '
 '`SOURCE_COMPARISON.md` retains the full supplied-source diffs: job.py, operator.py, and runner.py differ. '
 'The two supplied export stagers differ as modules, while parse_done and stage_export have identical function text. '
 'The production payload supplies every unchanged source in this build.\n')
cfg=read_config(OUT/'package');old=read(OUT/'AUDIT_R1.json')
inputs=read(ROOT/'in/prod_pkg/a/1.json');raw=(OUT/'export_544.json').read_bytes()
inputs['export_pin']=dict(path='a/export.json',sha256=digest(raw),bytes=len(raw))
write(OUT/'inputs_544.json',inputs)
audit=dict(status='built_offline_live_restore_unproved',token=cfg['token'],production_archive=old['archive'],
 payload_sha256=cfg['payload_sha256'],payload_bytes=cfg['payload_bytes'],plan=cfg['plan_sha256'],
 logical=cfg['logical'],evaluator=code_hash(),reader=code_hash(OUT/'src/b/e2e_reader'),
 parity=reader_code_hash(OUT/'src/b'),item_set=read(OUT/'src/items/devs1_routed.json')['item_set_sha256'],
 raw_inputs_544=sha(OUT/'inputs_544.json'),canonical_inputs_544=canonical({k:v for k,v in inputs.items() if k!='resume'}),
 changed_members=changed,identical_members=len(rows)-len(changed),production_members=len(a),package_members=len(b),
 preparation_receipt_h11_supplied=False,submerge_sha256=sha(OUT/'submerge.py'))
write(OUT/'AUDIT.json',audit)
write(OUT/'DELIVERY_SHA256.json',{name:sha(OUT/name) for name in
      ('fill_export.py','node_check.py','submerge.py','export_544.json','export_TEMPLATE.json','inputs_544.json')})
print(json.dumps(audit,indent=2))
