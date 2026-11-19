"""Emit gaps when any necessary evidence is absent; preserve exact source pins."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from survey import ROOT,W,K,N,OUT,TREE,read,pin,save,collect_pins
from student_pilot import r2_policy as P

survey=read(OUT/'SURVEY.json')
resolution=read(OUT/'PIN_RESOLUTION.json')
source_map={r['path']:r for r in survey['sources']}
missing=[];seen=set()
for r in resolution['references']:
    if r['local_matches'] or r['sha256'] in seen:continue
    if r['path'].endswith(('.sqlite','heads.json','artifact.json','receipt.json')):
        seen.add(r['sha256'])
        missing.append(dict(status='MISSING',name=Path(r['path']).name,expected_path=r['path'],expected_sha256=r['sha256'],
            referenced_by=r['referenced_by'],reference_field=r['field'],
            reason='No byte-identical copy in the bounded metadata/SQLite survey. Scene-level membership cannot be recovered from counts.'))

cfg=read(K/'b02e4385.json')
ancestor=cfg['init_artifact']['artifact'];depth=cfg['depth_init']
parent_requirements=[]
for label,spec in [('inherited m200 checkpoint',ancestor),('depth VC step 400',depth)]:
    parent_requirements.append(dict(status='MISSING',name='Complete training-scene manifest and parent membership receipt for '+label,
        expected_location=str(Path(spec['path']).parent),identity_pin=spec,exact_filename=None,
        reason='The named checkpoint metadata is missing. Its manifest filename and hash cannot be recovered without inventing them.'))
parent_requirements.append(dict(status='MISSING',name='Complete step-544 parent scene membership across pointing, pose, routing and vqa',
    expected_location=str(K.parent/'runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd'),exact_filename=None,
    reason='Surviving receipts bind exact rows.sqlite files and selection indices, but the five parent stores and upstream membership receipts are missing.'))

common_inputs=[pin(OUT/'SURVEY.json'),pin(OUT/'PIN_RESOLUTION.json'),pin(OUT/'INTERSECTIONS.json'),pin(__file__)]
summaries={}
(OUT/'records').mkdir(exist_ok=True)
for slot in (*P.LINEAGE,*P.EXTERNAL,*P.NEW):
    specific=[];unrecoverable=[]
    if slot in P.LINEAGE:
        specific=missing if slot!='depth_init_vc' else [r for r in missing if r['expected_sha256']==depth['sha256']]
        unrecoverable=parent_requirements if slot!='depth_init_vc' else [parent_requirements[1]]
        conclusion='MISSING: complete authenticated ancestor scenes and parent membership; no lineage overlap count is asserted.'
        rests='Step-544 artifact, LEG-S1 config, preparation receipts and BENCH v2.'
    elif slot=='geometry_tower':
        unrecoverable=[dict(status='MISSING',name='Upstream geometry tower release/weights/config identity and actual frozen optimizer inventory',
            expected_location='The N component registry and production geometry_online encoder binding; no such binding in n1fix2/inputs/config.json.',
            exact_filename=None,reason='Tower selection notes and freezing code do not establish an actual run-bound frozen parameter inventory.')]
        conclusion='MISSING: upstream asset identity tied to an actual frozen optimizer inventory.'
        rests='N configuration, G3T/GF1 freezing code and tower selection receipts.'
    elif slot=='segmenter':
        sam=ROOT/'work/extracted/b08_partA/code/pricekit/vendor/SAM3_RECEIPT.json'
        unrecoverable=[dict(status='MISSING',name='Actual SAM3 frozen optimizer inventory bound to checkpoint 9999e234 and N',
            expected_location='N component registry / segmenter runtime inventory alongside the SAM3 release receipt.',exact_filename=None,
            referenced_by=pin(sam),reason='SAM3_RECEIPT.json supplies checkpoint and revision identities, but no frozen inventory and no certified cache-time binding.')]
        conclusion='MISSING: actual frozen inventory and N runtime binding for the identified SAM3 checkpoint.'
        rests='SAM3_RECEIPT.json: upstream revision and checkpoint hash.'
    elif slot=='data_rows_r2':
        rp=read(N/'row_sources.json')
        for q in collect_pins(rp):
            if 'membership' in q['field'] or 'coverage' in q['field'] or 'host' in q['field']:
                specific.append(dict(status='MISSING',name=Path(q['path']).name,expected_path=q['path'],expected_sha256=q['sha256'],referenced_by=pin(N/'row_sources.json')))
        unrecoverable=[dict(status='MISSING',name='Complete independent alias/scene coverage for 119375 unresolved rows in rows.sqlite',
            expected_location='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite',exact_filename=None,
            referenced_by=pin(W/'w19/work/build19/inputs/component_rows.json'),
            reason='The full v7 store reproduces 119375 unresolved rows; no exhaustive mapping is available.'),
            dict(status='MISSING',name='Complete post-filter production family manifests and frame-host membership',
            expected_location=str(N/'row_sources.json'),exact_filename=None,
            reason='The named routing slices have zero observed scope intersections, but they do not cover all production families or unresolved v7 rows.')]
        conclusion='MISSING: full production coverage; 119375 of 204413 v7 rows have unresolved scene identities.'
        rests='Deferred component_rows record, v7 store, row-family receipts and recomputed partial intersections.'
    else:
        unrecoverable=[dict(status='MISSING',name='GF1 connector parameter inventory and complete training-scene/exclusion receipt',
            expected_location=str(N/'registry.json')+'#/heads_gf1_connector/record',exact_filename=None,
            reason='N disables fusion, but r2_policy still requires this slot. No actual connector inventory and complete clean training/exclusion receipt establish the required PROVEN_CLEAN claim.')]
        conclusion='MISSING: connector inventory and clean population/exclusion evidence. Configuration says none; the slot remains required.'
        rests='N config geometry_connector=none and r1_components deferred-slot rule.'
    inputs=common_inputs+[dict(path=p,sha256=source_map[p]['sha256']) for p in survey['slots'][slot]]
    save(OUT/'gaps'/f'{slot}.json',dict(schema='sb-component-evidence-gap-v1',component=slot,status='MISSING',record_written=False,
        inputs=inputs,conclusion=conclusion,rests_on=rests,missing_sources=specific,
        requirements_without_recovered_source_filename=unrecoverable,
        checked_banks=None if slot in P.LINEAGE else [],overlaps=None,
        overlap_status='MISSING: complete parent membership unavailable' if slot in P.LINEAGE else 'No complete component-level overlap conclusion',
        partial_checks=dict(path=str(OUT/'INTERSECTIONS.json'),sha256=pin(OUT/'INTERSECTIONS.json')['sha256']),
        gate_decision='No record is bound; r2_policy must refuse this slot.'))
    summaries[slot]=dict(status='MISSING',gap=pin(OUT/'gaps'/f'{slot}.json'),conclusion=conclusion,rests_on=rests)
save(OUT/'RECORD_DECISIONS.json',dict(schema='sb-record-decisions-v1',inputs=common_inputs,records_written=0,slots=summaries,
    note='No evidence record is fabricated to satisfy the permissive shape checker. Missing source filenames are explicitly unknown where surviving pins do not name them.'))
# Preserve registry fields exactly; only evidence-qualified records may fill record slots.
registry=read(N/'registry.json')
save(OUT/'kit/registry.json',registry)
save(OUT/'REGISTRY_PROVENANCE.json',dict(schema='sb-registry-copy-v1',inputs=[pin(N/'registry.json'),pin(OUT/'RECORD_DECISIONS.json')],
    registry=pin(OUT/'kit/registry.json'),records_bound=[],reason='No slot has sufficient evidence; all original null bindings are preserved.'))
(ROOT/'STATUS.md').write_text('Stage 2 complete. No production record meets the evidence requirements; all nine slots have MISSING gap files with source hashes and exact unavailable pins where recoverable. Fresh checks find zero scope intersections in 224 dev captures, three routing slices, and 85,038 resolvable v7 rows; 119,375 v7 rows remain unresolved. No parent-lineage intersection is claimed because its complete manifests are missing. The copied registry retains null records.\n')
print('records written: 0; gap files: 9')
