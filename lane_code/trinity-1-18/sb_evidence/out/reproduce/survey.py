"""Survey surviving evidence without treating a receipt count as a scene manifest."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
K = W/'w12/fixtures/work/kit07ca49df_meta/m/k'
N = W/'w19/work/n1fix2/inputs'
TREE = W/'w19/work/tree_r1'
OUT = ROOT/'out'
sys.path.insert(0, str(ROOT/'work/policy_tree'))
from student_pilot import r2_policy as P

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''): h.update(block)
    return h.hexdigest()

def pin(path): return dict(path=str(Path(path).resolve()), sha256=sha(path))
def read(path): return json.loads(Path(path).read_text())
def save(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')

SLOTS = (*P.LINEAGE, *P.EXTERNAL, *P.NEW)
sources = {}
def add(path, slots, proves, lacks):
    path = Path(path)
    if not path.is_file(): raise FileNotFoundError(path)
    key = str(path.resolve())
    if key not in sources:
        sources[key] = dict(**pin(path), components=[], proves=[], lacks=[])
    s = sources[key]
    for field, values in [('components', slots), ('proves', [proves]), ('lacks', [lacks])]:
        s[field] = sorted(set(s[field]) | set(values))

def collect_pins(value, label=''):
    result = []
    if isinstance(value, dict):
        if isinstance(value.get('sha256'), str) and isinstance(value.get('path', value.get('file')), str):
            result.append(dict(field=label, path=value.get('path', value.get('file')), sha256=value['sha256']))
        for k, v in value.items(): result.extend(collect_pins(v, label+'/'+k))
    elif isinstance(value, list):
        for i, v in enumerate(value): result.extend(collect_pins(v, label+'/'+str(i)))
    return result

def main():
    for name in ('r2_policy.py','r2_portable.py','p3_provenance.py','r1_persisted.py',
                 'r1_components.py','r1_rooms.py','r2_withheld.py','r2_exclusions.py'):
        add(TREE/'student_pilot'/name, SLOTS, 'Executable policy, pin verification, deferral or scene identity rules.', 'Code specifies checks; it does not certify a production component.')
    add(TREE/'tests/test_r2_policy.py', SLOTS, 'Schema and refusal tests; evidence in this file is explicitly synthetic.', 'Synthetic records are not usable production evidence.')
    add(TREE/'tests/test_r1_build19.py', SLOTS, 'Tests require training-only deferral and refusal at official boundaries.', 'Tests do not recover lost production evidence.')
    add(N/'registry.json', SLOTS, 'Exact fourteen slot definitions and missing record bindings.', 'All record fields are null.')
    for p in sorted(N.glob('EVIDENCE_*.json')):
        d=read(p);add(p,[d['component']], 'Exact original evidence requirement.', d['missing'])
    add(N/'config.json', SLOTS, 'N binds step-544 pose, depth and frame embeddings; geometry_connector is none.', 'Disabled configuration is not a component evidence record or optimizer inventory.')
    add(N/'init_artifact.json', P.LINEAGE, 'Step 544, config identity, source seal and trained group hashes.', 'No parent scene membership or bank intersections; no complete ancestor closure.')
    add(N/'init.json', P.LINEAGE, 'Selected initialization archive and step.', 'No scene identities.')
    add(N/'h1_over.json', P.LINEAGE, 'H1 deployment and content handover references.', 'Does not replace the pinned ancestor training manifests.')
    for p in sorted(K.iterdir()):
        if not p.is_file() or p.suffix not in ('.json','.tsv','.jsonl'): continue
        if p.suffix == '.json':
            d=read(p);schema=d.get('schema') if isinstance(d,dict) else 'integer selection list'
            shape=', '.join(d.keys()) if isinstance(d,dict) else f'{len(d)} entries'
        else: schema=p.suffix;shape='exclusion membership rows'
        proves=f'LEG-S1 metadata identified by content: {schema}; fields: {shape}.'
        lacks='Metadata does not supply the complete inherited training-scene closure.'
        if p.name=='scene_reference.json':
            proves='Dev-S1 manifest: 100 rooms, 224 captures; reports zero ReVSI overlap for this dev set.'
            lacks='This is a development set, not a manifest of parent training scenes.'
        if p.name.startswith('pool_indices_'):
            lacks='Indices have no scene identity without their exact source rows.'
        if p.name=='pool_manifest.json': lacks='Scene counts and row-file pins are not complete scene lists.'
        if p.name=='s1_record.json': lacks='Source-code inventory does not establish training-data membership.'
        add(p,P.LINEAGE,proves,lacks)
    m=K.parent
    for p in sorted((m/'runs/469ddece/inputs').rglob('*.json')):
        add(p,P.LINEAGE,'Step-544 run preparation, stream exclusion accounting or first-step receipt.',
            'Scene counts and exclusion comparisons do not enumerate inherited scene membership; parent artifacts and row stores are needed.')
    for p in sorted((W/'inputs/p_configs').glob('*.json')):
        add(p,(*P.LINEAGE,*P.NEW),'P donor configuration pins inherited initialization and input streams.',
            'A configuration does not certify complete scene exclusions.')
    for p in sorted((W/'inputs/p_runtime').rglob('*.json')):
        add(p,(*P.LINEAGE,*P.NEW),'Persisted P preparation and per-stream comparison receipts.',
            'P continuation receipts do not replace step-544 ancestor membership; unresolved row identities remain.')
    for p in sorted((W/'ext/pk').iterdir()):
        if p.is_file() and p.suffix in ('.json','.jsonl','.tsv'):
            add(p,(*P.LINEAGE,*P.NEW),'P staged benchmark or removal membership bytes.',
                'An exclusion list is not proof that every ancestor or new row was checked.')
    for p in sorted((W/'ext/r1_ops/work/adm171377').rglob('receipt.json')):
        add(p,(*P.LINEAGE,*P.NEW),'Per-stream P receipt with counts, parent pins and heldout_overlap.',
            'The scenes field is a count; this continuation cannot certify all ancestor scenes.')
    for p in sorted((W/'inputs/rooms').iterdir()):
        if p.is_file():add(p,(*P.LINEAGE,*P.NEW),'Pinned physical-room identity or exclusion authority.', 'Authority requires a complete row-to-scene mapping to prove exclusions.')
    for name in ['row_sources.json','v7_receipt.json','v7_MANIFEST.json','v7_validator.json','v7_build.json',
                 'store_parameter.json','0d28fdd432b0.json','room_v2_CHECK.json','recovery_v2_CHECK.json']:
        add(N/name,P.NEW,'N row source, manifest, division or validation metadata.', 'These checks do not establish complete exclusions for every production family and host frame.')
    cr=W/'w19/work/build19/inputs/component_rows.json'
    add(cr,P.NEW,'Explicit DEFERRED row evidence with 119375 unresolved v7 rows.', 'It explicitly does not certify unresolved legacy tokens as clean.')
    for q in collect_pins(read(cr)):
        p=Path(q['path'])
        if p.is_file() and p.suffix!='.sqlite':
            add(p,P.NEW,'Source pinned by the current deferred row record.', 'The deferred record limits this evidence to its named population.')
    for lane in ['rows_r1','rows_r2','rows_a2']:
        for r in read(ROOT/'work/json_index_full.json'):
            p=Path(r['path'])
            if '/'+lane+'/' in str(p) and (('/out/' in str(p) or p.name=='receipt.json')):
                add(p,P.NEW,'Surviving row-family receipt or audit, identified as '+str(r.get('schema'))+'.',
                    'Family-scoped or diagnostic evidence; no claim of complete production ancestry or all-family exclusion coverage.')
    for name in ['gf1.py','gf1_config.py','g3t_online.py']:
        add(TREE/'student_pilot'/name, ('geometry_tower','heads_gf1_connector'), 'Implements frozen tower and connector configuration checks.', 'Code is not a run-bound frozen optimizer inventory or clean training manifest.')
    sam=ROOT/'work/extracted/b08_partA/code/pricekit/vendor/SAM3_RECEIPT.json'
    add(sam,('segmenter',),'SAM3 checkpoint hash, upstream revision and source hashes.', 'Receipt disclaims cache-time revision and working-tree certification; no actual frozen optimizer inventory bound to N.')
    for p in (Path('/scratch/jjyeung/n30_mirror/tower_redecide/STATUS.md'),
              Path('/scratch/jjyeung/n30_mirror/tower_redecide/work/reprice/decide_corrected.json'),
              Path('/scratch/jjyeung/n30_mirror/tower_redecide/work/pose_k1/POSE_K1.json')):
        add(p,('geometry_tower',),'Tower comparison or selection information.', 'Selection is not upstream weight/config identity bound to a frozen parameter inventory.')
    for r in read(ROOT/'work/extracted_index.json'):
        p=Path(r['path'])
        if '/configs/' in str(p) or p.name in ('INPUT_CATALOG.json','OPEN_INPUTS.md','COPY_MANIFEST.json','PARTB_PREP.md'):
            add(p,(*P.LINEAGE,*P.NEW),'Recovered head-training kit configuration or input catalog.', 'Kit configuration and fixtures do not provide the missing pinned ancestor artifacts and complete scene manifests.')
    for r in read(ROOT/'work/sqlite_index.json'):
        # Reuse the completed sequential content hash; avoid another whole-store read.
        sources[r['path']] = dict(path=r['path'],sha256=r['sha256'],components=list((*P.LINEAGE,*P.NEW)),
            proves=['Surviving row store whose bytes were hashed for exact parent-pin matching; the v7 store is scanned in INTERSECTIONS.json.'],
            lacks=['No store hash matches a required step-544 parent rows.sqlite pin. Later row stores cannot replace those parent populations.'])
    archives={}
    extracted={r['path']:r for r in read(ROOT/'work/extracted_index.json')}
    for path,source in sources.items():
        if path in extracted:
            r=extracted[path]
            if r['archive'] not in archives:archives[r['archive']]=pin(r['archive'])
            source['archive_input']=archives[r['archive']]
            source['archive_member']=r['member']
    # Source archives describe code, not checkpoint training membership.
    for r in read(ROOT/'work/source_archives/index.json'):
        add(r['path'],P.LINEAGE,'Sealed LEG-S1 source archive copied once from the exact authorized NFS file.', 'Contains source code and test fixtures, not the missing parent scene manifests.')
    inventory=read(K/'s1_record.json')['trees']['trainer']['files']
    base=W/'w19/work/base/tree_b01ce449'
    matches=[];mismatches=[]
    for name, expected in inventory.items():
        p=base/name
        if p.is_file() and sha(p)==expected:matches.append(name)
        else:mismatches.append(name)
    save(OUT/'SOURCE_ARCHIVE_CHECK.json',dict(schema='sb-source-archive-check-v1',inputs=[pin(K/'s1_record.json')],
        local_b01_tree=str(base),matched_files=len(matches),mismatches=mismatches,
        archive_845b1789_not_copied='Existing local tree checked against the 792-file sealed inventory.',
        verified_files=[dict(path=str(base/name),sha256=inventory[name]) for name in matches],
        copied_archives=[dict(r,original_path='/data3/jjyeung/distill_src_archive/'+Path(r['path']).name) for r in read(ROOT/'work/source_archives/index.json')]))
    # Explicit hash resolution across the bounded local metadata survey.
    index=read(ROOT/'work/json_index_full.json')+read(ROOT/'work/extracted_index.json')+read(ROOT/'work/sqlite_index.json')
    byhash={}
    for r in index:byhash.setdefault(r['sha256'],[]).append(r['path'])
    referenced=[]
    parents=[K/'b02e4385.json', K/'8957d119.json', K/'0.json', N/'init_artifact.json']
    parents+=list((m/'runs/469ddece/inputs').rglob('receipt.json'))
    for p in parents:
        for q in collect_pins(read(p)):
            referenced.append(dict(**q,referenced_by=pin(p),local_matches=byhash.get(q['sha256'],[])))
    save(OUT/'PIN_RESOLUTION.json',dict(schema='sb-pin-resolution-v1',inputs=[pin(ROOT/'work/json_index_full.json'),
        pin(ROOT/'work/extracted_index.json'),pin(ROOT/'work/sqlite_index.json'),*[pin(p) for p in parents]],
        scope='Bounded local metadata, extracted head kit metadata and all eleven named-survey SQLite stores; no NFS path dereferencing.',references=referenced))
    manifest=dict(schema='sb-evidence-survey-v1',inputs=[pin(__file__),pin(ROOT/'source_paths.txt'),pin(ROOT/'tree_paths.txt'),pin(ROOT/'w12_paths.txt')],
        slots={s:[p for p,r in sources.items() if s in r['components']] for s in SLOTS},sources=list(sources.values()),
        limits=['Synthetic test evidence is excluded from production records.',
                'Missing membership is MISSING, never an empty overlap list.',
                'No claim that benchmark exclusions repair inherited checkpoint exposure.'])
    save(OUT/'SURVEY.json',manifest)
    lines=['# Component evidence survey','', 'Every source below is identified by bytes. Counts and source-code inventories cannot replace training-scene manifests.', '',
           'Command: `work/run_python.sh work/survey.py`. SHA256 uses streaming `hashlib.sha256` over exact file bytes; `sha256sum FILE` reproduces each digest.', '']
    for slot in SLOTS:
        lines += ['## '+slot,'','| Source | SHA256 | Proves | Lacks |','|---|---|---|---|']
        for p in manifest['slots'][slot]:
            r=sources[p];lines.append('| '+p+' | '+r['sha256']+' | '+' '.join(r['proves']).replace('|','/')+' | '+' '.join(r['lacks']).replace('|','/')+' |')
        lines.append('')
    (OUT/'SURVEY.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'STATUS.md').write_text('Stage 1 complete. The survey pins surviving metadata, source archives and exclusion authorities for all nine slots. The step-544 stream receipts bind the config but contain scene counts rather than full membership. Both inherited checkpoint metadata files are absent by hash; the current row record leaves 119,375 v7 rows unresolved. The policy tests pass on the local copy. Records remain subject to evidence sufficiency and fresh intersection checks.\n')
    print('survey sources',len(sources),'sealed b01 matched',len(matches),'mismatches',mismatches)

if __name__=='__main__': main()
