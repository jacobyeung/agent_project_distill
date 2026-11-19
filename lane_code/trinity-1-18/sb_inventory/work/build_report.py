"""Build evidence inventories and conservative component-gap drafts."""
import json,hashlib,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];T=R/'work/sealed/work/tree_r1';I=R/'out/inventories'
E=Path('/scratch/jjyeung/orch_n30/sb_evidence');W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
sys.path.insert(0,str(T))
from student_pilot import r2_policy as P
def pin(p):
    p=Path(p).resolve();h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return dict(path=str(p),sha256=h.hexdigest())
def read(p):return json.loads(Path(p).read_text())
def write(p,value,inputs):
    value['inputs']=[pin(x) for x in sorted(set(map(Path,inputs)))]
    Path(p).write_text(json.dumps(value,indent=2)+'\n')
def claim(text,*paths):return dict(claim=text,sources=[pin(p) for p in paths])
cfgpath=R/'work/sealed/work/build19/inputs/kit_config.json';cfg=read(cfgpath)
pol=T/'student_pilot/r2_policy.py';ctr=T/'student_pilot/carrier_c1.py';run=T/'student_pilot/carrier_c1_run.py'
g3=T/'student_pilot/tower_read.py';sam=T/'student_pilot/sam3_tower.py';gf=T/'student_pilot/gf1.py'
receipt=E/'work/extracted/b08_partA/code/pricekit/vendor/SAM3_RECEIPT.json'
sr=read(receipt);op=read(I/'optimizer.json');gp=read(I/'g3t_parameters.json')
base=[Path(__file__),cfgpath,pol,T/'tests/test_r2_policy.py',ctr,run,T/'student_pilot/r1_training.py',T/'student_pilot/r1_components.py',I/'optimizer.json',R/'out/PACKAGE.json']
# Record all literal release pins and related loader references in the shipped tree,
# C-prime configs/runtime metadata and named mirror receipt lanes. No weight IO.
need=re.compile(r'd460957|5aeb2acd|c55e91a|9999e234|5dd401d|df1ea59a|8223a095|SAM3_RECEIPT|sam3\.pt|thatbrguy/g3t')
scan=[]
for root in [T,W/'inputs/p_configs',W/'inputs/p_runtime',Path('/scratch/jjyeung/n30_mirror/tower_redecide'),
             Path('/scratch/jjyeung/n30_mirror/b04_e2ehook'),Path('/scratch/jjyeung/n30_mirror/gt_audit')]:
    scan.extend(p for p in root.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.md') and p.stat().st_size<2_000_000)
scan += [receipt]
aws=E/'aws_sources'
if aws.exists():scan.extend(p for p in aws.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.md') and p.stat().st_size<2_000_000)
hits=[];hitpaths=[]
for p in sorted(set(scan)):
    text=p.read_text(errors='replace')
    lines=[dict(line=i,text=l) for i,l in enumerate(text.splitlines(),1) if need.search(l)]
    if lines:hits.append(dict(source=pin(p),occurrences=lines));hitpaths.append(p)
configs=[]
for p in [cfgpath,R/'work/sealed/work/n1fix2/inputs/config.json',*sorted((W/'inputs/p_configs').glob('*.json')),W/'inputs/p_runtime/A_runtime_673bc60f.json']:
    c=read(p);configs.append(dict(source=pin(p),keys={k:c.get(k,'ABSENT') for k in ['geometry_connector','geometry_online','sam3','sam3_tower','tower','pose_source','frame_count','frame_layout','training_mode']}))
b18=Path('/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_r1');comparisons=[]
for name in ['r2_policy.py','carrier_c1.py','carrier_c1_run.py','g3t_online.py','tower_read.py','sam3_tower.py','gf1.py','gf1_config.py','r1_training.py','r1_components.py']:
    a=T/'student_pilot'/name;b=b18/'student_pilot'/name
    comparisons.append(dict(file=name,w19=pin(a),b18=pin(b) if b.exists() else dict(path=str(b),status='MISSING'),equal=pin(a)['sha256']==pin(b)['sha256'] if b.exists() else False))
write(I/'release_pin_index.json',dict(schema='sb-release-pin-index-v1',occurrences=hits,config_keys=configs,b18_comparison=comparisons,
    search_scope='All .py/.json/.md files below the listed source/runtime/mirror directories, each below 2 MB; archive contents snapshotted separately. Tests and other arms are labeled by source paths, not treated as N configuration.',
    scanned_files=len(set(scan)),aws_sources_present=aws.exists(),unavailable_survey_sources=[r for r in read(E/'out/PIN_RESOLUTION.json')['references'] if any(s in str(r).lower() for s in ['g3t','sam3','geometry_tower'])]),
    [Path(__file__),E/'out/SURVEY.json',E/'out/PIN_RESOLUTION.json',*hitpaths,*[Path(c['source']['path']) for c in configs],*[b18/'student_pilot'/r['file'] for r in comparisons if 'sha256' in r['b18']]])
geometry_claims=[
 claim('G3T repository thatbrguy/g3t, revision c55e91a04f1cbbad67359072536351201fd19e8b.',T/'student_pilot/c1r_ref.py',g3),
 claim('FrozenG3TTower checks exact weight, config and vendor digests; strict checkpoint keys and shapes; eval().requires_grad_(False); _load and run use inference_mode.',g3),
 claim('N kit has geometry_connector=none and no geometry_online; training load_model does not attach the separate routed tower.',cfgpath,ctr,run),
 claim('Full G3T meta reconstruction has 1472 parameter tensors, 1406749212 elements, zero trainable tensors and zero optimizer members; parent.train() leaves the attached tower in eval mode.',I/'g3t_parameters.json'),
 claim('Optional G3TEncoder finetune mode can unfreeze aggregator parameters and parameter_groups places them in geometry_encoder. This path is not selected by N; GF1 requires frozen mode.',T/'student_pilot/g3t_online.py',ctr,gf,T/'student_pilot/r1_training.py')]
write(I/'geometry_tower.json',dict(schema='sb-component-inventory-v1',component='geometry_tower',status='MISSING_RUN_BINDING',
    release=dict(name='G3T',repository='thatbrguy/g3t',revision='c55e91a04f1cbbad67359072536351201fd19e8b',version='No separate version recorded',
      assets=[dict(name='model.safetensors',sha256='d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702',pin_kind='loader-required; not hashed weights'),
              dict(name='config.json',sha256='5aeb2acd008d41a1cac52e10216fbf35e8dfeb2ce26b89bb24e7ccc4ee0817d7',pin_kind='loader-required; config bytes not supplied')],
      source_sha256=gp['source_digest_observed'],license='Some vendored layer headers say Apache License Version 2.0; other files refer to a missing root LICENSE. Full G3T release/weight license is MISSING; do not extrapolate layer licenses.'),
    training_registered_parameters=[],optimizer_parameter_tensors=0,reconstructed_parameters=pin(I/'g3t_parameters.json'),claims=geometry_claims,
    binding='N kit and exact sealed loader code are identified. No N runtime settings/manifest certifies that the pinned pretrained tower was attached or used.'),
    base+[g3,T/'student_pilot/c1r_ref.py',T/'student_pilot/g3t_online.py',gf,I/'g3t_parameters.json',I/'release_pin_index.json',T/'student_pilot/g3t_vendor/vggt/layers/attention.py',T/'student_pilot/g3t_vendor/vggt/models/aggregator.py'])
sam_claims=[claim('SAM3 loader pins revision and checkpoint to the same identities as SAM3_RECEIPT.json.',sam,receipt),
    claim('Sam3Tower is a plain Python owner; _freeze sets eval and requires_grad False; encode and _detect use inference_mode; parent train and optimizer traversal do not manage its backend.',sam),
    claim('N training load_model never attaches SAM3. Disabled attach_sam3_tower is a no-op. No SAM3 parameters occur in the reconstructed student.',sam,run,I/'optimizer.json'),
    claim('Receipt certifies six source hashes but explicitly does not certify working-tree cleanliness or cache-time revision.',receipt)]
write(I/'segmenter.json',dict(schema='sb-component-inventory-v1',component='segmenter',status='MISSING_ARCHITECTURE_AND_RUN_BINDING',
    release=dict(name='SAM 3 image model',version='3 (name); no separate package version recorded',revision=sr['sam3_upstream_revision'],
                 assets=[dict(path=sr['checkpoint_path'],sha256=sr['checkpoint_sha256'],bytes=sr['checkpoint_bytes'],pin_kind='receipt and loader; weights not read')],
                 source_files=sr['source_files'],source_origin=sr['sam3_source_origin'],license='MISSING: not recorded in supplied release receipt'),
    architecture_parameters=None,architecture_parameter_count=None,training_registered_parameters=[],optimizer_parameter_tensors=0,
    claims=sam_claims,missing_sources=[dict(name=k,sha256=h,expected_location=sr['sam3_source_origin']+'/'+k,status='MISSING from supplied local inputs; NFS source not accessed') for k,h in sr['source_files'].items()],
    binding='No supplied N runtime settings/manifest binds this checkpoint to an actual SAM3 backend or certified mask-cache generation. Missing architecture is not represented as an empty model.'),base+[sam,receipt,I/'release_pin_index.json'])
gf_claims=[claim('R1 validate refuses non-none geometry_connector or any geometry_online. CarrierC1 creates auxiliary_heads.gf1 only when geometry_online contains gf1.',cfgpath,T/'student_pilot/r1_training.py',ctr),
    claim('The reconstructed N student has no GF1 module, parameter tensor or optimizer member.',I/'optimizer.json'),
    claim('The strict policy still requires heads_gf1_connector as new_training, phase both, verdict PROVEN_CLEAN and exclusions_complete true; there is no disabled/not-applicable verdict.',pol),
    claim('R1 training may skip the absent connector or defer it; official reads still require its lost record.',T/'student_pilot/r1_training.py',T/'student_pilot/r1_components.py')]
write(I/'heads_gf1_connector.json',dict(schema='sb-component-inventory-v1',component='heads_gf1_connector',status='ABSENT_IN_N_POLICY_GAP',
    release=dict(name='GF-1 connector (local implementation)',revision='N sealed source tree 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa',
                 assets=[],license='No component-specific license recorded; no GF1 weights loaded by this N configuration'),
    parameters=[],parameter_tensors=0,parameter_numel=0,optimizer_parameter_tensors=0,claims=gf_claims,
    clean_record_possible_now=False,reason='Absence proves that this constructor creates no connector training population. It does not authenticate the lost component receipt or establish exclusions_complete for the mandatory slot. No not-applicable policy branch exists.'),base+[gf,I/'release_pin_index.json'])
missing={
 'geometry_tower':[dict(name='N-bound pretrained G3T runtime settings and frozen inventory receipt',exact_filename=None,expected_location='N inference artifact manifest / geometry_tower component evidence; original receipt filename not recorded',status='MISSING'),
                   dict(name='model.safetensors and config.json binding',expected_location='N inference artifact g3t/model.safetensors and g3t/config.json (layout documented by b04 e2e_reader)',status='MISSING binding; weight bytes not required for meta probe')],
 'segmenter':[dict(name='sam3/model_builder.py and dependencies',expected_location=sr['sam3_source_origin']+'/sam3/model_builder.py or a hash-matching staged copy under supplied /scratch inputs',status='MISSING in permitted local inputs'),
              dict(name='N-bound SAM3 frozen inventory and runtime/cache provenance receipt',exact_filename=None,expected_location='N segmenter component record alongside SAM3_RECEIPT.json',status='MISSING')],
 'heads_gf1_connector':[dict(name='Complete clean training/exclusion receipt for mandatory heads_gf1_connector slot',exact_filename=None,expected_location='N component registry evidence; original receipt filename not recorded',status='MISSING'),
                       dict(name='Policy treatment of an absent connector',expected_location='student_pilot/r2_policy.py new_training branch',status='MISSING not-applicable branch; no policy change made')]}
for slot in missing:
    spec=P.slots()[slot]
    requirements=dict(schema='r2-component-evidence-v1',component=slot,component_class=spec['component_class'],phase='both',inputs='nonempty list of resolvable path/sha256 pins')
    requirements.update(dict(verdict='EXEMPT_FROZEN',frozen=True) if slot in P.EXTERNAL else dict(verdict='PROVEN_CLEAN',exclusions_complete=True))
    write(R/'drafts'/f'{slot}.GAP.json',dict(schema='sb-component-evidence-gap-v1',component=slot,status='MISSING',record_written=False,
          required_record_fields=requirements,missing_sources=missing[slot],supported_claims=read(I/f'{slot}.json')['claims'],
          inventory=pin(I/f'{slot}.json'),decision='No r2-component-evidence-v1 draft and no registry binding: required production claim is not fully supported.'),base+[I/f'{slot}.json',E/'out/gaps'/f'{slot}.json'])
# Exercise the actual strict parser with missing records and false declarations.
checks=[];probe=R/'work/policy_probes';probe.mkdir(exist_ok=True)
for slot in missing:
    try:P.record(P.slots()[slot]);raise AssertionError('accepted missing record')
    except ValueError as e:checks.append(dict(component=slot,case='missing_record',result='REFUSE',message=str(e)))
    spec=P.slots()[slot]
    v=dict(schema=spec['expected_schema'],component=slot,component_class=spec['component_class'],phase='both',inputs=[pin(cfgpath)],synthetic=True)
    v.update(dict(verdict='EXEMPT_FROZEN',frozen=False) if slot in P.EXTERNAL else dict(verdict='PROVEN_CLEAN',exclusions_complete=False))
    path=probe/(slot+'.json');path.write_text(json.dumps(v))
    try:P.record({**spec,'record':pin(path)});raise AssertionError('accepted false evidence')
    except ValueError as e:checks.append(dict(component=slot,case='required_boolean_false',result='REFUSE',message=str(e)))
write(R/'out/POLICY_CHECKS.json',dict(schema='sb-policy-checks-v1',checks=checks,passed=len(checks),official_items_read=0,
    note='Synthetic refusal probes only. Existing policy test source was inspected; full suite not run.'),base+[T/'student_pilot/r2_portable.py',*probe.glob('*.json')])
(R/'STATUS.md').write_text('All three component inventories and GAP drafts are complete. Six strict-policy refusal probes passed. The G3T meta inventory is complete, GF1 is absent, and SAM3 architecture/run binding remains missing. No evidence record or registry binding is justified; final hash and archive validation remain.\n')
print('release matches',len(hits),'policy refusals',len(checks),'draft gaps',len(missing))
