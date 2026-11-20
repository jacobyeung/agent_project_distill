"""Read-only source census; all products are written below the working directory."""
import ast, collections, copy, html, json, math, re, resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(15<<30,15<<30))
C=Path.cwd(); B=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); T=B/'w24j/work/tree_r1'; P=B/'w24j/work/build24m4j/p_tree'; K=B/'w24j/out/kit_n_go'
cfg=json.loads((C/'n_go_c.json').read_text()); overlay=dict(cfg,min_pixels=16384,max_pixels=147456,frame_count=32)
graph=json.loads((C/'call_graph.json').read_text()); rows=json.loads((C/'reachable_raw.json').read_text())
index=json.loads((C/'source_asset_index.json').read_text()); asts={}; texts={}; positions={}
def source(file,old=False):
    path=(P if old else K if file.startswith('b/') else T)/file
    if not path.is_file():return ''
    return path.read_text()
def parse(file,old=False):
    key=(file,old)
    if key not in asts:
        texts[key]=source(file,old);asts[key]=ast.parse(texts[key]); positions[key]={}
        def walk(n,fn='',parents=()):
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):fn=(fn+'.' if fn else '')+n.name
            positions[key][id(n)]=(fn,parents)
            for ch in ast.iter_child_nodes(n):walk(ch,fn,parents+(n,))
        walk(asts[key])
    return asts[key]
def guards_of(file,node,old=False):
    parse(file,old); parents=positions[(file,old)][id(node)][1]; guards=[]
    child=node
    for parent in reversed(parents):
        if isinstance(parent,ast.If):
            g=ast.unparse(parent.test); guards.append(g if child in parent.body else 'NOT ('+g+')')
        child=parent
    return guards[::-1]
def is_reachable(file,fn):
    mod=('kit.'+Path(file).stem) if file.startswith('b/') else file[:-3].replace('/','.').removesuffix('.__init__')
    sym=mod+'.'+(fn or '<module>')
    while sym not in graph['reachable'] and sym.count('.')>mod.count('.')+1:sym=sym.rsplit('.',1)[0]
    return graph['reachable'].get(sym,[])
def named(file,node,expression,kind='named_refusal',phase=None):
    fn=positions[(file,False)][id(node)][0]; gs=guards_of(file,node)
    candidates=[]
    for old in ast.walk(parse(file,True)):
        if type(old)==type(node) and ast.unparse(old)==ast.unparse(node):
            candidates.append(dict(line=old.lineno,function=positions[(file,True)][id(old)][0],guards=guards_of(file,old,True)))
    exact=next((p for p in candidates if p['guards']==gs),None)
    return dict(file=file,line=node.lineno,function=fn,exception=expression,guards=gs,except_context=[],mark='SAME' if exact else 'NEW',p_sites=candidates,phases=phase or is_reachable(file,fn),kind=kind)
# Include subprocess-boundary raises without traversing C code as though it were P's child.
file='b/rb.py'
for node in ast.walk(parse(file)):
    fn=positions[(file,False)][id(node)][0]
    if isinstance(node,ast.Raise) and fn in ('import_probe','load_modules','child'):
        rows.append(named(file,node,ast.unparse(node.exc) if node.exc else 'reraise',kind='raise',phase=['routing']))
# A requested reader helper is not used by the launch; keep it explicitly identified.
file='student_pilot/b7_inputs.py'
for node in ast.walk(parse(file)):
    if isinstance(node,ast.Raise) and positions[(file,False)][id(node)][0]=='reader_layout':
        r=named(file,node,ast.unparse(node.exc),kind='requested_helper',phase=['reader_family']);r['reachability']='Requested comparison helper; no call from N training.';rows.append(r)
# Named non-exception refusals and assertion sites in the reached source closure.
files=sorted({r['file'] for r in rows}|{'student_pilot/s1_first_step.py','student_pilot/trace_grammar.py'})
for file in files:
    tree=parse(file)
    for node in ast.walk(tree):
        fn=positions[(file,False)][id(node)][0]
        if not is_reachable(file,fn):continue
        exp=None;kind='named_refusal'
        if isinstance(node,ast.Assert):exp='AssertionError('+ (ast.unparse(node.msg) if node.msg else repr('assert '+ast.unparse(node.test)))+')';kind='assert'
        elif isinstance(node,ast.Call):
            call=ast.unparse(node.func)
            if call=='sys.exit' and node.args:
                exp='SystemExit('+ast.unparse(node.args[0])+')';kind='exit'
            if call=='print' and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str) and re.fullmatch('[A-Z0-9_]+(?:TIMEOUT|REFUSED|MISSING)',node.args[0].value):
                exp=repr(node.args[0].value)
            if call in ('errors.append','reasons.append','refusals.append','verdicts.append','errors.insert') and node.args:
                value=node.args[-1]
                if isinstance(value,(ast.Constant,ast.BinOp,ast.JoinedStr)) and not (isinstance(value,ast.Constant) and not isinstance(value.value,str)): exp=ast.unparse(value)
            if file=='student_pilot/trace_grammar.py' and call=='add' and node.args and isinstance(node.args[0],ast.Constant):exp='trace_grammar:'+str(node.args[0].value)
            if file=='student_pilot/trace_grammar.py' and call=='Violation' and node.args and isinstance(node.args[0],ast.Constant):exp='trace_grammar:'+str(node.args[0].value)
        elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='reason' for t in node.targets) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):exp=repr(node.value.value)
        elif isinstance(node,ast.Return) and fn.rsplit('.',1)[-1] in ('reason','deferred','fla_check') and isinstance(node.value,(ast.Constant,ast.BinOp,ast.JoinedStr)) and not (isinstance(node.value,ast.Constant) and not isinstance(node.value.value,str)):exp=ast.unparse(node.value)
        if exp is not None:rows.append(named(file,node,exp,kind))
# These names share a dynamic raise site; preserve the names without multiplying site counts.
dynamic_names={('student_pilot/row_text_audit.py',121):['rows_lane_rule_only_text:<family>:non_ascii_authored_think','rows_lane_rule_only_text:<family>:gravity_guard','rows_lane_rule_only_text:<family>:heading_threshold_status','rows_lane_rule_only_text:<family>:runtime_box_status','rows_lane_rule_only_text:<family>:tower_scale_rule','rows_lane_rule_only_text:<family>:tower_scale_provenance_not_from_head'],('student_pilot/s1_first_step.py',32):['nonfinite_or_missing_components','nonfinite_or_missing_stream_means','nonfinite_or_missing_gradient_norms']}

excluded=[]; kept=[]
for r in rows:
    f,fn=r['file'],r['function']; why=None
    if f=='student_pilot/b7_inputs.py' and fn in ('module_trainability','assert_policy'):why='N has no b7_inputs; load_model/export guard these helpers on that key.'
    if f=='student_pilot/r1_components.py' and fn=='guard':why='Official evaluation only; r1_persisted.admission defaults official=False and N has no r2_evaluation.'
    if f=='launch_r1/p_handover_receipt.py':why='N uses persisted_files plus step400 export-only policy; the legacy collect/verify_receipt fallback is not selected.'
    if f=='student_pilot/r2_mix.py' and fn in ('preflight','plans','validate_table','table'):why='N r2_sampling.schema=r1-sampling-v1; r2_mix dispatches to r1_mix and returns before the R2 fallback.'
    if f=='student_pilot/r2_contract.py' and fn.startswith('Admission.'):why='N has no r2_membership; sealed R2 membership reader is not constructed.'
    if f=='launch_r1/entry.py' and fn=='frame_host':why='CPU mode-p entry only; N and discovery use modes r/q through production_proof and begin_host.'
    if '__name__' in ' '.join(r['guards']) and not f.startswith('b/'):why='Imported module; its standalone CLI main guard is false.'
    if why:excluded.append(dict(r,exclusion=why))
    else:kept.append(r)
rows=kept

Q='/tmp/q_22c714e1'; X='/project/community/jjyeung/okh7/x_22c714e1'
locators={
 'rows':f'{Q}/v.json -> preparation -> streams.<stream>.(database|sources|indices); r2_sampling.population/indices. Inspect the actual SQLite row, target and RGB pins, not receipt counts.',
 'frames':f'{Q}/r.json.frame_roots and job STUDENT_FRAME_ROOT_MAP/K* mapping; the row student_input.frames pins and the preparation frame_inventory.sqlite/hash sample under {Q}/p/q/p.',
 'handover':f'{Q}/e.json and {Q}/v.json.r1_training.p_run/persisted_files/init_artifact; donor metadata is authenticated locally, but heads/full_weights and model tensors must be checked on Orchard.',
 'population':f'{Q}/p/q/b/reader_filters.json and produced r2_sampling.population/indices in {Q}/v.json; all post-filter rows in preparation streams, including both pose sources.',
 'host':f'{Q}/p/q/RESULT.json, {Q}/p/q/host.json, {Q}/p/hr.json, {Q}/r.json and {Q}/p/i/staging.json; live job namespace, modes, binaries and mount results.',
 'census':f'{Q}/c5.json and {X}/o/$SLURM_JOB_ID/live/c0.json..c4.json; actual source/admitted rows via {Q}/p/q/ss.json and v.json.preparation.',
 'review':f'{X}/n_r/review.json (directory mode0700, file mode0600, owner/job identity); evidence h0.json,s0..s3,e0..e7,c0..c4 under {X}/o/$SLURM_JOB_ID/live, and {Q}/v.json.',
 'copy':f'{Q}/p/q/r/ checkpoint/export complete markers and payloads; {X}/o/$SLURM_JOB_ID, node-root live_spool/free space, and {X}/n_s/sess.json; live remote generation/range receipts.',
 'runtime':f'{Q}/v.json, {Q}/p/q/r/inputs/first_step_*.json, {Q}/p/q/r/metrics_*.jsonl, actual model/optimizer tensors, rank env, CUDA/NCCL and the first optimizer result on Orchard.',
 'disk':f'The filesystem holding {Q}/p/q/r and node-root live_spool on Orchard; free bytes from statvfs plus per-rank optimizer/model tensor measurements printed in checkpoint_disk_guard/export_disk_guard.',
 'pins':f'{Q}/u/<sha256> and {Q}/p/q/u/<sha256>, selected through {Q}/v.json and {Q}/p/i/staging.json; the exact pinned file bytes and resolved path metadata.',
 'routing':f'{Q}/n.json, {Q}/p/routing_selection.json, {Q}/p/q/selection/(materialization.json,receipt.json,rows.sqlite); P reconstruction {Q}/p/q/base_imports.json,base_mounts.json,base/rows.sqlite (expected4e8e6c04...). Mode-r comparison also uses pr_imports.json/pr/rows.sqlite under the same q root; discovery maps its dr directory onto Q for mode r.',
}
def category(r):
    f,fn=r['file'],r['function']
    if f in ('b/pc.py','b/gc.py') or f=='launch_r2/persistence.py':return 'copy'
    if f=='b/rv.py':return 'review'
    if f in ('b/cs.py','b/sv.py'):return 'census'
    if f in ('b/rb.py','b/pl.py','b/rg.py','b/rd.py','b/sc.py') or 's1_routing' in f or 's1_pool' in f:return 'routing'
    if f.startswith('b/') or f.startswith('launch_r1/entry') or f.startswith('launch_r1/production'):return 'host'
    if any(s in f for s in ('r1_handover','r1_persisted','r1_absence','p_opener','p_export','r2_openers')):return 'handover'
    if 'checkpoint_space' in f:return 'disk'
    if any(s in f for s in ('r1_population','r1_loader','r1_mix','r1_coverage','r1_counting','r1_rooms','r1_direction','r1_launch22')):return 'population'
    if any(s in f for s in ('r2_frames','orchard_paths','pose_samples')):return 'frames'
    if any(s in f for s in ('r2_policy','r1_components','p3_provenance','source_seal','launch_r2/staging')):return 'pins'
    if f=='student_pilot/carrier_c1_run.py':
        if fn in ('checkpoint','export','complete_states','existing_export','checkpoint_options'):return 'disk'
        if fn.startswith('Rows.') or fn in ('fetch','check_row','encode_plan_rows','prepared','prepare'):return 'rows'
        return 'runtime'
    if any(s in f for s in ('carrier_c1.py','full_ft','camera_head','point_depth_head','auxiliary_losses','fixed_readout','p3_heads','fsdp_training','s1_first_step')):return 'runtime'
    return 'rows'
def refusal_name(r):
    exp=r['exception']
    if exp=='reraise':return 'reraise:'+r['function']
    try:
        n=ast.parse(exp,mode='eval').body
        if isinstance(n,ast.Call) and n.args:n=n.args[0]
        if isinstance(n,ast.Constant) and isinstance(n.value,str):return n.value
        if isinstance(n,ast.BinOp):
            a=n
            while isinstance(a,ast.BinOp):a=a.left
            if isinstance(a,ast.Constant) and isinstance(a.value,str):return a.value+'<dynamic>'
        if isinstance(n,ast.JoinedStr):return ''.join(v.value if isinstance(v,ast.Constant) else '{'+ast.unparse(v.value)+'}' for v in n.values)
    except Exception:pass
    return exp

checks={}
for file in ('offline_results.json','offline_more_results.json','metadata_results.json','supplemental_results.json'):
    for x in json.loads((C/file).read_text()):checks[x['name']]=dict(x,evidence_file=file)
cov=set(tuple(x) for x in json.loads((C/'metadata_coverage.json').read_text()))
def put(r,verdict,evidence,actual=None,patched=None):
    r['verdict']=verdict;r['evidence']=evidence
    r['actual_verdict']=actual or verdict;r['pixels_added_verdict']=patched or verdict
    if verdict=='PASSES':r['deciding_input']=None
def safe_eval(s,env):
    if s.startswith('NOT ('):s='not '+s[4:]
    tree=ast.parse(s,mode='eval')
    # No source functions, filesystem access, or arbitrary attributes may execute.
    allowed={'get','keys','values','items','startswith','endswith','isdecimal','isdigit','isascii','issuperset','issubset','isfinite','fullmatch','compile'}
    for n in ast.walk(tree):
        if isinstance(n,ast.Call):
            if isinstance(n.func,ast.Attribute) and n.func.attr not in allowed:raise ValueError('unsafe predicate call')
            if isinstance(n.func,ast.Name) and n.func.id not in {'type','int','bool','str','len','set','dict','list','tuple','any','all','sum','range','sorted','min','max','isinstance','float'}:raise ValueError('unknown predicate call')
    built=dict(type=type,int=int,bool=bool,str=str,len=len,set=set,dict=dict,list=list,tuple=tuple,any=any,all=all,sum=sum,range=range,sorted=sorted,min=min,max=max,isinstance=isinstance,float=float)
    return eval(compile(tree,'<census-static>','eval'),dict(__builtins__=built,**env))

# A small set of constants/conditions is proved against the decoded capsule.
card=json.loads(Path(index[cfg['r1_training']['mix']['sha256']]).read_text())
common_env=dict(cfg=cfg,recipe=cfg['recipe'],math=math,re=re,world=4,world_size=4,frame_count=32,training_mode='final',start_step=0,steps=1000,smoke_steps=None,resume_pin=None,export_binding=None)
relaxed=[]
for r in rows:
    r.setdefault('kind','raise');r['name']=refusal_name(r);r['names']=dynamic_names.get((r['file'],r['line']),[r['name']])
    r['condition']=' AND '.join('('+g+')' for g in r['guards']) or ('exception handler: '+', '.join(r.get('except_context',[])) if r.get('except_context') else 'unconditional at this site; see caller and preceding control flow')
    r['comparison_note']='Exact exception and enclosing conditions found in P.' if r['mark']=='SAME' else 'No matching explicit refusal site in P source.'
    # Generalized 64-frame code is identical on N's pinned 32-frame branch.
    if r['mark']=='STRICTER':
        f=r['file'];r['mark']='SAME'
        r['comparison_note']='Retained P check. C expands the accepted domain or parameterizes the same check; no additional refusal on the common branch. Both exact predicates are recorded in guards/p_sites.'
        if f in ('student_pilot/decoupled_v.py','student_pilot/carrier_c1_routing.py','student_pilot/carrier_c1_data.py') or r['function']=='check_row':r['comparison_note']='Same condition after substituting N frame_count=32; C also supports 64 frames.'
        else:relaxed.append(dict(file=f,line=r['line'],p_sites=r['p_sites'],condition=r['condition']))
    if r['file']=='student_pilot/checkpoint_space.py' and r['name'].startswith('Insufficient '):
        r['mark']='STRICTER';r['comparison_note']='P checks native remaining state/export bytes + reserve. C adds retained_archive_copies*(remaining states/exports plus tar headers); N sets this to1. Required bytes are strictly greater for nonempty saves.'
    renamed={('student_pilot/camera_config.py',101):'Camera max_groups must be an integer in 16..48',('student_pilot/carrier_c1_data.py',632):'C1 preservation rows require 32 pinned native frames (VQA: 64 with anchor_slots)'}
    if (r['file'],r['line']) in renamed:
        old_name=renamed[(r['file'],r['line'])]
        for old in ast.walk(parse(r['file'],True)):
            if isinstance(old,ast.Raise) and old_name in ast.unparse(old):
                r['p_sites']=[dict(line=old.lineno,function=positions[(r['file'],True)][id(old)][0],guards=guards_of(r['file'],old,True))]
                r['mark']='SAME';r['comparison_note']='P has the same 32-frame/max_groups predicate; C broadens support to64 and updates the error wording. No additional N rejection.'
                break
    cat=category(r);r['input_class']=cat;r['deciding_input']=locators[cat]
    r['verdict']='UNDECIDED offline' if r['mark']!='SAME' else 'NOT_REEVALUATED'
    r['actual_verdict']=r['pixels_added_verdict']=r['verdict'];r['evidence']='Static source condition only; production operand values were not executed or observed here.'
    # A false enclosing capsule condition proves the branch is inactive. Do not
    # evaluate fields that native preparation is expected to replace.
    dynamic_fields={'preparation','host_receipt','review','store_hashes','continuation_identity','continuation_receipt','row_plan_sha256','routing_vocabulary','r2_sampling','r2_scene_rebuild','scene_coverage','streams','admission'}
    env=dict(common_env)
    if r['file']=='student_pilot/r1_training.py' and r['function']=='validate':env.update(value=cfg['r1_training'],card=card,scale=0.04,stop=None)
    if r['file']=='student_pilot/r1_persisted.py' and r['function']=='init_policy':env['value']=cfg['r1_training']
    if r['file']=='student_pilot/b7_inputs.py' and r['function']=='layout':env['result']={k:overlay[k] for k in ('min_pixels','max_pixels','frame_count','frame_layout','frame_markers')}
    if r['file']=='trace_format/contracts.py':env.update(enabled=True,value=0.3)
    if r['file']=='student_pilot/fixed_readout.py':env['heading_plane_min']=0.3
    if r['file']=='student_pilot/carrier_c1_run.py' and r['function']=='validate':env.update(gx=None,overrides=cfg['camera_overrides'],permitted_overrides={'weight_focal','weight_scale'})
    if r['file']=='student_pilot/stop_control.py':env['limit']=None
    if r['file']=='student_pilot/r1_mix.py' and r['function']=='plans':env.update(world=4,start_step=0,steps=1000)
    for g in r['guards']:
        if any(re.search(r"['\"]"+re.escape(k)+r"['\"]",g) for k in dynamic_fields):continue
        try:value=safe_eval(g,env)
        except Exception:continue
        if not value:
            put(r,'PASSES','Static predicate is false on N: '+g);break
    if r['kind']=='assert':r['condition']='assertion fails when NOT ('+ast.unparse(next(n.test for n in ast.walk(parse(r['file'])) if isinstance(n,ast.Assert) and n.lineno==r['line']))+')'
    # Successful metadata-only execution establishes tested metadata branches,
    # never large tensor payloads or newly prepared rows.
    f,ln,fn=r['file'],r['line'],r['function']
    if (f,ln) not in cov and f in ('student_pilot/r1_persisted.py','student_pilot/r1_handover.py','student_pilot/r1_absence.py','student_pilot/r1_launch22.py','b/rb.py'):
        native_funcs={
            'student_pilot/r1_persisted.py':{'init_policy','export_only','verify','verify.read'},
            'student_pilot/r1_handover.py':{'donor','_donor','prepared_stream_identity','stream_identity','stream_identity.check','compare_configs'},
            'student_pilot/r1_absence.py':{'configuration'},
            'student_pilot/r1_launch22.py':{'validate_removals'},
            'b/rb.py':{'routing_status','statuses'},
        }
        if fn in native_funcs[f]:
            # Metadata verification deliberately skipped payload paths.
            weight_sensitive=f=='student_pilot/r1_persisted.py' and (fn=='verify.read' or ln in (145,188))
            if not weight_sensitive:put(r,'PASSES','Native metadata_checks.py completed this validator with authenticated P metadata and N pins; weights=False, no production rows or model weights checked.')
    if f=='student_pilot/r1_training.py' and 'predicate:r1_training.py:'+str(ln) in checks:
        v=checks['predicate:r1_training.py:'+str(ln)]
        if v.get('result',{}).get('refuses') is False:put(r,'PASSES','Native predicate evaluation in offline_more_results.json; full R1 validate stops at unavailable row_sources and is not certified.')
    if f=='student_pilot/b7_inputs.py' and fn=='layout':
        if ln==37:put(r,'REFUSES','Native layout(actual) raises processor_resolution_pin_missing: min_pixels/max_pixels are null; native layout(pixel overlay) passes. Known fourth refusal.',actual='REFUSES',patched='PASSES')
        else:put(r,'PASSES','Native layout(pixel overlay) passes: 16384 <=147456; frame_count exact int32, duplicate, frame_markers=True. Original missing pins short-circuit before this check.',actual='NOT_REACHED',patched='PASSES')
    if f=='student_pilot/b7_inputs.py' and fn=='reader_layout':
        r['verdict']=r['actual_verdict']=r['pixels_added_verdict']='UNDECIDED offline';r['evidence']='reader_layout(overlay,overlay) passed, but no independent reader config is supplied and the helper is not called by N training.';r['deciding_input']='The evaluation reader config/receipt layout fields on Orchard, if this optional reader helper is invoked; compare all five fields to v.json. No reader is part of the requested training path.'
    if f=='student_pilot/r1_handover.py' and ln==186:
        put(r,'REFUSES','Native compare_configs(P,N,metadata=[P preparation]) passes. With max_pixels147456/min_pixels16384 it raises P_EXPORT_CONFIG_DIFFERENCE:max_pixels. A min-only test independently raises P_EXPORT_CONFIG_DIFFERENCE:min_pixels. P effective defaults are None; these keys are not exempt.',actual='PASSES',patched='REFUSES');r['names']=['P_EXPORT_CONFIG_DIFFERENCE:max_pixels','P_EXPORT_CONFIG_DIFFERENCE:min_pixels']
    if f=='student_pilot/r0_exclusion.py' and ln==31:put(r,'PASSES','Native reserve() verified SHA256 f7c458... of C r0_scenes.json; 6398 scene names and110 rooms loaded (offline_results.json).')
    if f=='student_pilot/r2_grammar.py' and fn=='check_shared':put(r,'PASSES','Native shared_grammar_digest passed in supplemental_results.json.')
    if f=='student_pilot/r1_coverage.py' and fn=='deferred_card':put(r,'PASSES','Native deferred_card on the authenticated N card passed in metadata_results.json.')
    if f=='student_pilot/carrier_c1_run.py' and ln==94:put(r,'PASSES','Native checkpoint plan matches N: planned_full_states14, extra_full_states2, exports7, reserve200000000000, retained_archive_copies1.')
    if f=='b/h.py' and r['name']=='E85':put(r,'PASSES','Decoded N world_size4 and init_policy step400_export_weights_fresh_v1.')
    if f=='b/pl.py' and ln==20:
        put(r,'REFUSES','Native pl.selection_pin on supplied kit_n_go raises R1_ROUTING_SELECTION_PIN_MISSING. k/h.json carries required_parameter, not path/sha256. This is the documented pre-arming state: mode r can run, but mode q requires the reviewed selection to be armed and the kit resealed. Post-arming content remains unverified here.')
    if f=='launch_r1/production_proof.py' and ln==76 and card.get('counting_admission')=='procedure_only_v1':
        put(r,'PASSES','Static comparison of authenticated N mix card: counting_admission=procedure_only_v1.')
    if f=='launch_r1/production_proof.py' and ln in (118,121):
        put(r,'PASSES','Kit b/z.py:246 sets memory_gib=180 and device=cuda:0; 180 is an integer in 8..512 and cuda:0 is accepted. No memory allocation or CUDA execution was tested.')
    if f=='launch_r1/entry.py' and ln==72 and cfg['r1_training'].get('init_policy')=='step400_export_weights_fresh_v1':
        put(r,'PASSES','Native init_policy passed. The valid non-null fresh-init policy takes export_only, bypassing this legacy export-only rejection branch.')
    if f=='b/a.py' and r['name']=='E03' or f=='b/u.py' and r['name']=='E03':put(r,'PASSES','Launch control GO=true; discovery GO=false is deliberately nontraining.')
    if f=='student_pilot/carrier_c1_data.py' and ln==165:
        r['verdict']=r['actual_verdict']=r['pixels_added_verdict']='UNDECIDED offline';r['evidence']='Pixel overlay sets expected frame_count32; no complete production row bodies were inspected. All 32 actual frames must be present for each row, including rows formerly allowed by single-image/short-clip branches.';r['deciding_input']=locators['rows']+' Check len(row.student_input.frames)==32 at encode_layout_row.'
    if f=='student_pilot/r0_exclusion.py' and ln==62:r['deciding_input']=locators['rows']+' Check every row with C reserve().check(row,"dense_frames"); Rows.row also checks the stream under r1_training.'
    if f=='student_pilot/extent_receipt.py' and fn=='Extents.__init__' and checks.get('extent_receipt_schema',{}).get('status')=='PASS':put(r,'PASSES','Native Extents construction authenticated N extent_receipt and verified full-extent-receipt-v1; it did not audit row contents.')
    if f=='student_pilot/r1_components.py' and fn=='deferred' and checks.get('deferred_component_records',{}).get('status')=='PASS':put(r,'PASSES','Native r1_components.deferred verified N deferred component metadata in supplemental_results.json; official evaluation remains a separate boundary.')
    r.setdefault('reachability','Conservative source call closure; conditions retain inactive alternatives unless explicitly excluded. All downstream conditions are conditional on prior stages succeeding.')
    if r['mark']=='SAME' and r['verdict']=='NOT_REEVALUATED':r['evidence']='P contains this refusal; no additional-input verdict was requested for SAME. This is not a production pass.'

# Explicit external-process failure edges are useful for the previously observed
# scipy/bwrap refusals; library internals are not recursively enumerated.
for file in ('b/rb.py','b/t.py','b/g.py','b/sc.py'):
    for node in ast.walk(parse(file)):
        if not isinstance(node,ast.Call) or ast.unparse(node.func)!='subprocess.run' or not any(k.arg=='check' and isinstance(k.value,ast.Constant) and k.value.value is True for k in node.keywords):continue
        fn=positions[(file,False)][id(node)][0]
        if not is_reachable(file,fn) and fn!='child':continue
        r=dict(file=file,line=node.lineno,function=fn,exception='subprocess.CalledProcessError',name='subprocess.CalledProcessError:'+file+':'+str(node.lineno),names=['subprocess.CalledProcessError:'+file+':'+str(node.lineno)],guards=guards_of(file,node),condition='The child process exits nonzero: '+ast.unparse(node),except_context=[],mark='NEW',p_sites=[],phases=is_reachable(file,fn) or ['routing'],kind='external_process',comparison_note='Kit helper is absent in P.',verdict='UNDECIDED offline',actual_verdict='UNDECIDED offline',pixels_added_verdict='UNDECIDED offline',evidence='No subprocess was launched. User reports the prior P rebuild completed; this does not test a new job environment.',input_class='routing',deciding_input=locators['routing']+' Check actual bwrap stderr and child return code in the Orchard job log.',reachability='Explicit external-process boundary, including bwrap namespace/proc and missing-library failures.')
        rows.append(r)
# The capsule is shell with embedded Python; record its explicit refusal/exit sites
# without executing it or treating k/j.json as a plain JSON config.
for file,path in [('k/j.json (decoded launch shell)',C/'n_go_j.sh'),('job.sh',K/'job.sh')]:
    for ln,line in enumerate(path.read_text().splitlines(),1):
        if not ('raise SystemExit' in line or ('return 3' in line) or ('echo E87' in line) or "trap 'exit 143'" in line or "trap 'exit 138'" in line or line.startswith('assert ')):continue
        name=('SystemExit:'+line.split('raise SystemExit(',1)[1].rstrip(')') if 'raise SystemExit(' in line else 'E87' if 'echo E87' in line else 'sha differs' if 'return 3' in line else 'signal termination' if "trap 'exit" in line else 'AssertionError:torchrun missing')
        r=dict(file=file,line=ln,function='job_shell',exception=line.strip(),name=name,names=[name],guards=[],condition=line.strip(),except_context=[],mark='NEW',p_sites=[],phases=['kit','stop'] if 'signal' in name else ['kit'],kind='shell_boundary',comparison_note='The N kit shell boundary is absent from P source.',verdict='UNDECIDED offline',actual_verdict='UNDECIDED offline',pixels_added_verdict='UNDECIDED offline',evidence='Shell inspected only; not executed.',input_class='host',deciding_input=locators['host']+' Also inspect staged init heads/weights, model/frame archive bytes, torchrun console script and actual job exit/signal.',reachability='Explicit shell/heredoc boundary in decoded launch capsule or job.sh.')
        rows.append(r)

pin_fields={
 'student_pilot/r1_coverage.py':['r1_training.row_sources','r1_training.wording_exclusion','r1_training.camera_wording_exclusion','r1_training.v7_k1_union'],
 'student_pilot/r1_rooms.py':['r1_training.room_authority','r1_training.room_audit','r1_training.row_sources','r1_training.direction_twins'],
 'student_pilot/r1_direction_twins.py':['r1_training.direction_twins','r1_training.v7_k1_union'],
 'student_pilot/r1_components.py':['r1_training.component_rows','r1_training.registry'],
 'student_pilot/r2_policy.py':['r1_training.registry'],
 'student_pilot/r1_absence.py':['r1_training.registry','init_artifact.artifact'],
 'student_pilot/r1_training.py':['r1_training.mix','r1_training.registry','r1_training.row_sources'],
 'student_pilot/r1_launch22.py':['remove_files'],
 'student_pilot/r1_mix.py':['r1_training.mix'],
 'student_pilot/extent_receipt.py':['extent_receipt'],
 'student_pilot/r2_scene_bindings.py':['dev_scene_exclusions','benchmark_scene_exclusions','remove_files'],
}
def get_field(path):
    value=cfg
    for key in path.split('.'):value=value[key]
    return value
def pin_entries(value,field):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:
            h=value['sha256']; yield dict(config_field=field,sha256=h,orchard_path=Q+'/'+value['path'] if not value['path'].startswith('/') else value['path'],local_replica=index.get(h))
        else:
            for key,v in value.items():yield from pin_entries(v,field+'.'+key)
    elif isinstance(value,list):
        for i,v in enumerate(value):yield from pin_entries(v,field+'.'+str(i))
for r in rows:
    r['input_pins']=[pin for field in pin_fields.get(r['file'],[]) for pin in pin_entries(get_field(field),field)]
    if r['verdict']=='UNDECIDED offline' and r['input_pins']:
        r['deciding_input']+=' Capsule authorities: '+'; '.join(p['config_field']+'='+p['orchard_path']+' (sha256 '+p['sha256']+')' for p in r['input_pins'])+'. Use v.json for any produced replacements.'

# Discovery has a distinct export-only proof configuration and no trainer/copier.
for r in rows:
    r['config_variant']='launch N unless explicitly described otherwise'
    if r['file'].startswith('b/'):
        qpath=B/'w24j/out/kit_qd'/r['file']
        r['kit_variants']=['n_go','n']+(['qd','q'] if qpath.is_file() else [])
        if r['file']=='b/h.py' and r['name']=='E85':r['kit_variants']=['n_go','n']
        if r['file']=='b/rv.py' and r['line']>=281:r['kit_variants']=['n_go','n','q'];r['reachability']+=' Discovery qd returns0 at rv.py:279 before the review-wait loop.'
qd_cfg=json.loads((C/'qd_c.json').read_text())
qd_condition="cfg.get('world_size') != 4 or cfg.get('r1_training',{}).get('proof_mode') != 'q' or cfg.get('r1_training',{}).get('init_policy') is not None"
qd_pass=not eval(qd_condition,{'cfg':qd_cfg})
rows.append(dict(file='qd/b/h.py',line=11,function='<module>',exception="ValueError('E85')",name='E85 (discovery proof mode)',names=['E85 (discovery proof mode)'],guards=[qd_condition],condition=qd_condition,except_context=[],mark='NEW',p_sites=[],phases=['q_prepare'],kind='raise',comparison_note='Discovery host handoff is absent in P; launch b/h.py has a different policy guard.',verdict='PASSES' if qd_pass else 'REFUSES',actual_verdict='PASSES' if qd_pass else 'REFUSES',pixels_added_verdict='PASSES' if qd_pass else 'REFUSES',evidence='Evaluated against decoded qd_c.json: world4, proof_mode=q, init_policy absent.',input_class='host',input_pins=[],deciding_input=None,reachability='Discovery mode q handoff only.',config_variant='qd/q',kit_variants=['qd','q']))
rows.sort(key=lambda r:(r['file'],r['line'],r['kind'],r['name']))
for i,r in enumerate(rows,1):r['id']='C%04d'%i
counts=collections.Counter(r['mark'] for r in rows);verdicts=collections.Counter(r['verdict'] for r in rows)
matrix={mark:dict(collections.Counter(r['verdict'] for r in rows if r['mark']==mark)) for mark in counts}
result=dict(schema='census24-v1',tree_c=str(T),tree_p=str(P),launch_kit=str(K),config=str(C/'n_go_c.json'),pixel_overlay=dict(min_pixels=16384,max_pixels=147456,frame_count=32),counts=dict(rows=len(rows),by_mark=dict(counts),by_verdict=dict(verdicts),by_mark_and_verdict=matrix,actual=dict(collections.Counter(r['actual_verdict'] for r in rows)),pixels_added=dict(collections.Counter(r['pixels_added_verdict'] for r in rows))),scope='Explicit raises/assertions and named refusal sites in the conservative source call closure, plus selected external process boundaries. One row per source site; parameterized names are retained. Not a proof that dynamic dispatch or third-party implicit exceptions cannot add failures.',rows=rows,excluded=excluded,relaxed_existing_predicates=relaxed,orchard_inputs=locators,checks=[dict(name=x['name'],status=x['status'],output=x.get('output'),evidence_file=x['evidence_file']) for x in checks.values()])
(C/'CENSUS.json').write_text(json.dumps(result,indent=2)+'\n')

def esc(s):return html.escape(str(s)).replace('|','&#124;').replace('\n',' ')
lines=[f'Rows: {len(rows)}; SAME: {counts["SAME"]}; STRICTER: {counts["STRICTER"]}; NEW: {counts["NEW"]}.',
       'Verdicts (union of actual and requested pixel-overlay scenarios): '+', '.join(f'{k}: {v}' for k,v in sorted(verdicts.items()))+'.',
       'Actual capsule REFUSES: '+str(sum(r['actual_verdict']=='REFUSES' for r in rows))+'; pixel overlay REFUSES: '+str(sum(r['pixels_added_verdict']=='REFUSES' for r in rows))+'. Counts are source sites, not unique error strings or observed production failures.',
       'Mark × verdict: '+json.dumps(matrix,sort_keys=True)+'.','',
       'Three sites refuse across the two tested scenarios. The supplied launch kit has R1_ROUTING_SELECTION_PIN_MISSING: its documented arming step is still required before mode q. Actual N also refuses at processor_resolution_pin_missing. Adding only min_pixels=16384/max_pixels=147456/frame_count=32 clears layout but fails P_EXPORT_CONFIG_DIFFERENCE:max_pixels (min_pixels also differs). P pose_samples.py:37 uses exactly(16384,147456), so the pixel behavior can match while r1_handover.py:54–55,186 compares the explicit integers against None. The native P/N comparison passes without that overlay. This report does not inspect the concurrent build.',
       'N cannot run the requested one-GPU optimizer/checkpoint/export canary unchanged; see [CANARY.md](CANARY.md). Discovery requests all-rank no-grad forward checks on one GPU, which do not test Adam state or backward. Discovery has proof_mode=q and no fresh-init policy, so it resumes the proof at absolute step400; the launch N policy starts at0. Its checked rows therefore need not be N step1 rows.',
       '',
       'C is tree 0c7614c8; P is b83a8a35. Config capsules were decoded with the kit decoder and their content hashes checked. N has r1_training, r2_sampling, four ranks, global batch288, 32 duplicate frames, and zero own probability. P trained cprime_31abe087; the authenticated runtime config and preparation metadata establish its defaults.',
       'KIT_COMPARISON.json checks every b/ file across n_go,qd,n,q. n matches n_go. qd changes h.py to require proof_mode=q/no init_policy, omits trainer/copier files, and returns immediately after writing WAITING_REVIEW.json (rv.py:279); it does not await an independent PASS. Shared sites are counted once; the distinct qd E85 predicate has its own row. Launch review-wait checks remain launch-only for qd applicability.',
       'Scope: the table lists explicit source raises, assertions, named non-exception refusals, and selected subprocess failures. It follows the selected pipeline conservatively through first optimizer/checkpoint/export and stop. Dynamic/library exceptions are not exhaustively enumerable offline. Source-site counts are an upper bound where a row-dependent branch remains undecided. CENSUS.json retains exact guards, P sites, phase membership, tests and exclusions.',
       'SAME means the P predicate remains on the common applicable branch; generalized frame checks are evaluated at N frame_count32. Existing relaxed guards are retained as SAME with both predicates and a comparison note, never mislabeled STRICTER. JSON separately lists these relaxations. STRICTER includes the disk guard whose unchanged free<required predicate now includes an extra archive copy. NEW has no matching P refusal site.',
       'PASSES means a stated static condition or bounded native check passed; it is not whole-job approval. UNDECIDED offline names the deciding Orchard input. NOT_REEVALUATED applies only to existing P checks. NOT_REACHED marks later layout clauses short-circuited by the actual missing pins. Each downstream verdict assumes preceding blockers are resolved.',
       '',
       'The known four incidents map to P-selection reconstruction (b/rb.py:25,32; b/rg.py:34,40), isolated child imports (b/rb.py:150–175,400), external bwrap namespace/proc execution (b/rb.py:410–430,459), and processor layout (s1_routing.py:240 → carrier_c1_run.py:1257 → b7_inputs.py:37). The user reports P database4e8e6c04 rebuilt in full. No new bwrap or Orchard run occurred here.',
       'Optional-key branches: r1_training enables layout, row text/R0 checks, component evidence, handover, complete sampler binding and no substitution. contract_epoch is absent and defaults True; heading_plane_min defaults0.3. b7_inputs, geometry_online, mdg, r2_schedule and r2_membership are absent, so their feature-specific validators are not missing-input refusals. R1 deferred routing uses the base64-row quota; full extra routing slices remain off.',
       'Host/review/sampler/continuation placeholders are populated by mode q; their null capsule values are not counted as REFUSES. step400_export_weights_fresh_v1 legally accepts the export-only donor and starts a fresh optimizer at step0. Missing checkpoint-at-m400 is not a blocker. Deferred component records do not invoke the official-evaluation guard on this training path.',
       'The pixel-family row check is stricter than P encoding: encode_layout_row requires exactly32 row frames and runs the R0 reserve test once _b7_layout exists. Local layout validation passes after the overlay; full row/RGB/R0 outcomes remain undecided. reader_layout(overlay,overlay) passed but is an unused helper, not an independently verified evaluation reader.',
       'Other new row risks: OWN_VALUED_ROW_REFUSED; CAMERA_OBJECT_ABSOLUTE_DISTANCE_EXCLUDED; QUALITATIVE_TRACE_REQUIRED; ROOM_PROGRAM_REFUSED/ONE_LINE_ROOM_REFUSED/ROOM_TRACE_INVALID; rows_lane_rule_only_text and its six named reasons; EXTENT_ROW_UNAUDITED/EXTENT_BOX_NOT_FULL/EXTENT_REPAIR_UNCERTIFIED; R1 wordings, room/twin authorities, post-filter capacity and repeat limits. These depend on the actual final rows and their pinned audit records, not just the presence of configuration keys.',
       'The first checkpoint also retains a local archive: checkpoint_space.py adds retained_archive_copies=1 to the whole-leg guard. The plan is14+2 full states,7 exports, and200GB free reserve. The plan passes metadata checks; real free space and tensor bytes are undecided. Missing durable-upload binding alone is not a launch refusal because R1 takes local_only.',
       '',
       'Orchard locator keys used below (Q=/tmp/q_22c714e1, X=/project/community/jjyeung/okh7/x_22c714e1):']
lines.append('Q is the bwrap namespace for the job-local staging root ($SLURM_TMPDIR/q_22c714e1_$SLURM_JOB_ID). Output is Q/p/q/r according to b/pl.py:214,219 and final v.json.output; the operator pointer\'s Q/r shorthand is not the generated output path.')
for key,value in locators.items():lines.append(f'- **{key}**: {value}')
lines += ['', '| Pixel-family / nearby check | C site | Verdict with requested pixel overlay |','|---|---|---|',
          '| processor_resolution_pin_missing | b7_inputs.py:37 | PASSES; both pins are positive exact integers. Actual capsule REFUSES because both are null. |',
          '| processor_resolution_range | b7_inputs.py:39 | PASSES;16384 <=147456. |',
          '| frame_count_must_be_32_or_64 | b7_inputs.py:41 | PASSES; exact int32. |',
          '| training_frame_layout_mismatch | b7_inputs.py:43 | PASSES; duplicate and frame_markers=True. |',
          '| reader_training_layout_mismatch | b7_inputs.py:49 | UNDECIDED for an independent reader; helper is unused on this training path. Native same-config comparison passed. |',
          '| r0_authority_sha_mismatch | r0_exclusion.py:31 | PASSES; native authority hash verified. |',
          '| r0_room_refused:dense_frames:* | carrier_c1_data.py:163 → r0_exclusion.py:62 | UNDECIDED; every actual final row must miss the R0 reserve. |',
          '| row_training_frame_count_mismatch | carrier_c1_data.py:165 | UNDECIDED; each actual row must contain exactly32 frames. |',
          '| P_EXPORT_CONFIG_DIFFERENCE:max_pixels/min_pixels | r1_handover.py:186 | REFUSES; separate native tests reproduce both differing defaults. |']
lines += ['', 'Native evidence: [offline_results.json](offline_results.json), [offline_more_results.json](offline_more_results.json), [metadata_results.json](metadata_results.json), [supplemental_results.json](supplemental_results.json). ERROR results preserve their tracebacks; unavailable staged pins are offline limitations, not production failures. [FAILURES.log](FAILURES.log) records inspection-command failures. No weights, GPU computation, bwrap, network, or full production row scan ran.', '',
          'Table cells group sites only to keep this document below400 physical lines; every numbered site is a separate CENSUS.json row. The order inside a cell is ID, C line, name, condition, mark, verdict, evidence/deciding input. P source lines appear where matched.', '', '| File / phase | Refusal sites, conditions and verdicts |','|---|---|']
groups=collections.defaultdict(list)
for r in rows:groups[r['file']].append(r)
for file,group in groups.items():
    for offset in range(0,len(group),10):
        chunk=group[offset:offset+10];cell=[]
        for r in chunk:
            p='; P:'+','.join(str(x['line']) for x in r['p_sites']) if r['p_sites'] else '; P absent'
            detail=r['evidence'] if r['verdict']!='UNDECIDED offline' else 'Needs '+r['input_class']+' operands (locator above; exact config pin paths are in this ID\'s JSON input_pins/deciding_input).'
            if r['verdict']=='NOT_REEVALUATED':detail='Existing P check; no additional verdict.'
            cell.append(esc(f"{r['id']} :{r['line']} {r['name']} — IF {r['condition']} — {r['mark']}{p} — {r['verdict']} — {detail}"))
        lines.append('| '+esc(file)+' / '+esc(','.join(sorted({p for r in chunk for p in r['phases']})))+' | '+'<br><br>'.join(cell)+' |')
(C/'CENSUS.md').write_text('\n'.join(lines)+'\n')
unknown=[r for r in rows if r['verdict']=='UNDECIDED offline'];refused=[r for r in rows if r['verdict']=='REFUSES']
(C/'UNDECIDED_NAMES.txt').write_text('\n'.join(r['id']+' '+r['file']+':'+str(r['line'])+' '+','.join(r['names']) for r in unknown)+'\n')
(C/'FINAL.md').write_text('\n'.join([
    f"REFUSES {len(refused)} rows: "+'; '.join(','.join(r['names']) for r in refused)+f"; UNDECIDED {len(unknown)} rows: "+'; '.join(r['id']+' '+r['name'] for r in unknown)+'.',
    'The supplied kit needs its documented routing-selection arming step in both scenarios. Actual N also lacks pixel pins; the requested pixel overlay instead fails the P-export configuration comparison.',
    'CANARY c: unchanged C pins four ranks and R1 quotas; the existing one-GPU proof runs no-grad forward only.',
    'Native tests verified layout after the overlay, P donor metadata, original P/N config equivalence, R1 init policy, and selected configuration predicates.',
    'Prepared production rows, RGB, tensor payloads, reviewer approval, GPU execution, and available checkpoint/spool space remain unverified offline.',
    '[CENSUS.md](CENSUS.md) contains the grouped table; [CENSUS.json](CENSUS.json) contains individual sites, predicates, evidence and deciding Orchard inputs.',
    '[CANARY.md](CANARY.md) gives the exact prohibiting lines and the limits of the current forward proof.',
    'Recorded native failures and inspection errors remain in the evidence JSON/log files; no job or full row scan was run.',
])+'\n')
print(json.dumps(result['counts'],indent=2));print('CENSUS.md lines',len(lines));print('Explicit exclusions',len(excluded));print('Output bytes',sum(p.stat().st_size for p in C.rglob('*') if p.is_file()))
