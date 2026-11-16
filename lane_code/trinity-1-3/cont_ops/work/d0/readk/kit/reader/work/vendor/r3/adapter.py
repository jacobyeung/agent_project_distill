"""Frozen dev-S1 task/PNG adapter. No video decoder, network, or kit edits."""
import argparse
import collections
from functools import lru_cache
from decimal import Decimal, InvalidOperation
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
import tarfile
import io
sys.dont_write_bytecode=True
NUMERIC=('object_abs_distance','object_counting','object_size_estimation','room_size_estimation')
OFFICIAL_MC=('object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard','object_rel_distance','route_planning')
SCORERS={**dict.fromkeys(NUMERIC,'official_vsi_mra'),**dict.fromkeys(OFFICIAL_MC,'official_vsi_exact_match'),
         'relative_count':'generic_multiple_choice_exact_match','relative_size_object':'generic_multiple_choice_exact_match'}
EXCLUDED={'absolute_direction_object':'No direct-answer angular scorer in either kit',
          **dict.fromkeys(('camera_displacement','camera_movement_direction','camera_rotation'),
                          'No direct-answer scorer; routing-M question frame numbers are not mapped to the PLAN anchors')}
TIMING_VERSION='devS1_v2_real_timing'


@lru_cache(maxsize=1)
def timing_authority():
    root=Path(__file__).resolve().parent
    pins=json.loads((root/'PINS.json').read_text())
    for name in ('TIMING_AUTHORITY.json','FPS_RULE.json','FPS_AUTHORITY.source.json'):
        if sha(root/name)!=pins[name]:raise ValueError('Timing authority pin differs: '+name)
    return json.loads((root/'TIMING_AUTHORITY.json').read_text())['captures']


def validate_timing(capture):
    authority=timing_authority().get(capture.get('native'))
    if authority is None:raise ValueError('Capture has no pinned frame-rate authority')
    for key in ('fps','anchor_indices','total_num_frames','total_num_frames_lower_bound','timestamps','fps_rule','plan_alias','scene'):
        if capture.get(key)!=authority[key]:raise ValueError('Capture timing authority differs: '+key)
    if capture['fps']<=1:raise ValueError('Placeholder fps is refused')
    if capture['timestamps']!=[i/capture['fps'] for i in capture['anchor_indices']]:
        raise ValueError('Timestamps differ from source index / fps')
    if any(type(i) is not int or not 0<=i<capture['total_num_frames'] for i in capture['anchor_indices']):
        raise ValueError('Source index outside frame count')


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def dump(path,value,lines=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    text=(''.join(json.dumps(r,sort_keys=True,allow_nan=False)+'\n' for r in value) if lines else
          json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
    path.write_text(text)

def jsonl(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]

def option(value,options):
    if value is None:return None
    text=str(value).strip()
    labels={}
    for i,o in enumerate(options):
        m=re.fullmatch(r'\s*([A-Za-z])[.)]\s*(.*)',str(o),re.S)
        letter,body=(m[1].upper(),m[2]) if m else (chr(65+i),str(o))
        labels[letter]=body.strip()
    if text.upper() in labels:return text.upper()
    for letter,body in labels.items():
        if text.casefold() in (body.casefold(),(letter+'. '+body).casefold()):return letter
    raise ValueError('Label is not a supplied option: '+repr(value))

def number(value):
    try:n=Decimal(str(value).strip())
    except (InvalidOperation,ValueError):raise ValueError('Invalid numeric label: '+repr(value))
    if not n.is_finite():raise ValueError('Nonfinite numeric label')
    return n

def normalize_text(value):
    return ' '.join(str(value).casefold().split())

def option_contents(options):
    result={}
    for i,o in enumerate(options):
        m=re.fullmatch(r'\s*([A-Za-z])[.)]\s*(.*)',str(o),re.S)
        letter,body=(m[1].upper(),m[2]) if m else (chr(65+i),str(o))
        if letter in result:raise ValueError('Duplicate option letter')
        result[letter]=body
    return result

def selected_content(value,options):
    if value is None or not options:return None
    labels=option_contents(options)
    if str(value).strip().upper() in labels:return labels[str(value).strip().upper()]
    matches=[v for v in labels.values() if normalize_text(v)==normalize_text(value)]
    if len(matches)!=1:raise ValueError('Label has no unique option content')
    return matches[0]

def scoring_label(row,field):
    """Translate a released label into the option order shown to the model."""
    if field=='answer' or row['question_type'] in NUMERIC:return row.get(field)
    content=selected_content(row.get('released_answer'),row.get('released_options'))
    if content is None:return None
    matches=[k for k,v in option_contents(row['options']).items() if normalize_text(v)==normalize_text(content)]
    if len(matches)!=1:raise ValueError('Released content has no unique option in displayed order')
    return matches[0]

def effective_ground_truth(row):
    released=scoring_label(row,'released_answer')
    return released if released is not None else row.get('answer')

def strata(row):
    a,b=row.get('answer'),row.get('released_answer')
    if a is None or b is None:
        s='missing_both' if a is None and b is None else ('missing_canonical' if a is None else 'missing_released')
        agree=None;error=None
    elif row['question_type'] in NUMERIC:
        a,b=number(a),number(b)
        error=abs(a-b)/abs(b) if b else (Decimal(0) if a==0 else None)
        agree=(a==0 if b==0 else abs(a-b)<=Decimal('0.10')*abs(b));s='primary' if agree else 'disagreement'
    else:
        a=selected_content(a,row['options']);b=selected_content(b,row.get('released_options'))
        agree=None if b is None else normalize_text(a)==normalize_text(b)
        s='released_text_unavailable' if b is None else ('primary' if agree else 'disagreement');error=None
    return dict(key='devrows:'+row['id'],qid=row['id'],question_type=row['question_type'],room=row['room'],
                stratum=s,answer=row.get('answer'),released_answer=row.get('released_answer'),agree=agree,
                answer_content=selected_content(row.get('answer'),row.get('options')) if row['question_type'] not in NUMERIC else None,
                released_answer_content=selected_content(row.get('released_answer'),row.get('released_options')) if row['question_type'] not in NUMERIC else None,
                released_answer_in_options=scoring_label(row,'released_answer'),
                relative_difference=None if error is None else str(error),
                rule='MC: compare selected content in each label own option order, case/whitespace only; numeric: abs(answer-released)<=0.10*abs(released), released=0 requires answer=0; missing is unavailable')

def excluded_strata(rows):
    return [dict(key='excluded:'+r['qid'],qid=r['qid'],question_type=r['type'],room=r['room'],
                 stratum='excluded',reason=r['reason']) for r in rows]


def validate_membership(item,captures,withhold):
    if item['native'] not in captures:raise ValueError('Capture outside the 152 planned captures')
    if item['room'] not in withhold['rooms'] or item['native'] not in withhold['natives']:
        raise ValueError('Scene is not withheld')
    if captures[item['native']]['scene']!=item['scene']:raise ValueError('Capture/scene mismatch')
    if item['native'].startswith('d1/') and item['room']!=item['native'].rsplit('_',1)[0]:
        raise ValueError('ScanNet room mismatch')
    if item['native'].startswith('d2/') and item['room']!=item['native']:raise ValueError('ScanNet++ room mismatch')


def payload(root):
    root=Path(root).resolve();pins=json.loads((root/'PINS.json').read_text())
    for name,h in pins.items():
        p=root/name
        if p.parent!=root or sha(p)!=h:raise ValueError('Payload pin differs: '+name)
    rows=jsonl(root/'TASKS.jsonl');items=jsonl(root/'ITEMS.jsonl');exc=jsonl(root/'EXCLUDED.jsonl')
    cs={c['native']:c for c in json.loads((root/'FRAMES.json').read_text())['captures']}
    w=json.loads((root/'WITHHOLD_SCENES.json').read_text())
    if len(cs)!=152:raise ValueError('Plan must contain 152 captures')
    for capture in cs.values():validate_timing(capture)
    for it in items:validate_membership(it,cs,w)
    ids=[r['id'] for r in rows]+[r['qid'] for r in exc]
    if len(ids)!=len(set(ids)) or set(ids)!={i['qid'] for i in items}:raise ValueError('Item partition differs')
    fixed={i['qid']:i for i in items}
    for r in rows:
        it=fixed[r['id']]
        if (r['native'],r['room'],r['scene'],r['question_type'])!=(it['native'],it['room'],it['scene'],it['type']):
            raise ValueError('Task identity differs')
        if r['source_frame_indices']!=cs[r['native']]['anchor_indices']:raise ValueError('Task anchors differ')
        for key in ('fps','total_num_frames','total_num_frames_lower_bound'):
            if r.get(key)!=cs[r['native']][key]:raise ValueError('Task timing differs: '+key)
        if r['scorer']!=SCORERS[r['question_type']]:raise ValueError('Scorer differs')
        if r['answer'] is None:raise ValueError('Task has no canonical label')
        if r['ground_truth']!=effective_ground_truth(r):raise ValueError('Ground truth is not in displayed option order')
        if r['released_answer_in_options']!=scoring_label(r,'released_answer'):raise ValueError('Released label mapping differs')
        if r['stratum']!=strata(r)['stratum']:raise ValueError('Task stratum differs')
    if [strata(r) for r in rows]+excluded_strata(exc)!=jsonl(root/'STRATA.jsonl'):raise ValueError('Strata differ')
    keys=json.loads((root/'CELL_ITEMS.json').read_text())
    if keys['cp1m200']!=keys['f17'] or keys['f17']!=['devrows:'+r['id'] for r in rows]:raise ValueError('Cell membership differs')
    return root,pins,rows,cs


def copy_kit(source,dest):
    source=Path(source).resolve();dest=Path(dest).resolve();files={}
    # The evaluator's three documented code directories form the runtime closure.
    for sub in ('','evalpath','trainer'):
        for p in sorted((source/'evaluator'/sub).iterdir()):
            if p.is_file() and p.suffix in ('.py','.json'):
                rel=Path(sub)/p.name;raw=p.read_bytes();target=dest/'evaluator'/rel
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
                files[str(rel)]=raw
    for req in ('data.py','media.py','worker.py','merge.py','parity.py','scoring.py'):
        if req not in files:raise ValueError('Missing kit interface: '+req)
    # Match the kit's deterministic source archive format, and bind actual copied bytes.
    target=dest/'source.tar'
    with tarfile.open(target,'w',format=tarfile.PAX_FORMAT) as tf:
        for name,raw in sorted(files.items()):
            m=tarfile.TarInfo(name);m.size=len(raw);m.mode=0o444;m.mtime=0;tf.addfile(m,io.BytesIO(raw))
    dump(dest/'CODE_PINS.json',{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()})
    return sha(target)


def kit_import(root):
    root=Path(root).resolve()/'evaluator'
    if 'media' in sys.modules and Path(sys.modules['media'].__file__).parent!=root:
        raise ValueError('Use a separate Python process for each kit')
    sys.path.insert(0,str(root))
    return importlib.import_module('data'),importlib.import_module('media'),importlib.import_module('evalpath.official')


def validate_cell(cell,model):
    expected=dict(model=model,layout='duplicate' if model=='cp1m200' else 'spread',benchmarks=['devrows'],
                  frames=32,decoding='greedy',thinking=True,max_tokens=16384,name=TIMING_VERSION+'_'+model)
    if cell!=expected:raise ValueError('Cell protocol differs')


def check_model_specs(models,model):
    for key in ('base',model):
        s=models[key]
        pin=s['manifest'] if s['kind']=='snapshot' else s
        if not re.fullmatch('[0-9a-f]{64}',pin['sha256']) or pin['sha256']=='0'*64:raise ValueError('Unbound model pin')
        if not Path(s['path']).is_absolute():raise ValueError('Model path must be absolute')
    if models['base']['kind']!='snapshot':raise ValueError('Require base snapshot')
    expected={'cp1m200':('c1_export','c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67'),
              'f17':('archive','47308d99246bdf253a5d55ce9ec04a38a4fcc355092603a51e8de34604749eae')}
    if (models[model]['kind'],models[model].get('sha256'))!=expected[model]:raise ValueError('Checkpoint identity differs')
    if models['base']['manifest']['sha256']!='ae9247f7c316e7661bfbe4301c28d75b6871db7427d675b8e1cc4c0c41b4b252':
        raise ValueError('Base tokenizer/config snapshot differs')


def bind(args):
    root,pins,rows,captures=payload(args.payload)
    dest=Path(args.dest).resolve();dest.mkdir(parents=True,exist_ok=False)
    srcsha=copy_kit(args.kit,dest/'kit')
    data,media,official=kit_import(dest/'kit')
    model=args.cell;cell=json.loads((root/f'cells_{model}.json').read_text())[0];validate_cell(cell,model)
    if model=='cp1m200':importlib.import_module('think_settings').validate(cell)
    importlib.import_module('cells').frame_count(cell)
    models=json.loads(Path(args.models).read_text());check_model_specs(models,model)
    cfg=dict(models={k:models[k] for k in ('base',model)},cells=[cell],
             datasets=[dict(benchmark='devrows',rows=dict(path=str(root/'TASKS.jsonl'),sha256=pins['TASKS.jsonl']))],
             roots=dict(video_root=str(dest/'virtual_video_identity_only')),gpus=1,build_only=args.dry,
             max_tokens=16384,temperature=0,thinking=True,max_model_len=49152,max_seqs=32,inflight=16,
             smoke_items=0,engine_version='0.32.0',source_sha256=srcsha,
             devs1=dict(payload=str(root),pins=pins,adapter_sha256=sha(__file__),
                        model=args.cell,frames_root=str(Path(args.frames_root).resolve()),
                        code_pins_sha256=sha(dest/'kit/CODE_PINS.json'),
                        missing_policy='exclude missing canonical; score unavailable released labels only under canonical view',
                        timing_version=TIMING_VERSION,fps_rule='S1-FPS1',
                        timing_authority_sha256=pins['TIMING_AUTHORITY.json']))
    # Binder matches kit request binding: output is excluded from its hash.
    cfg['binding']=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()
    cfg['output']=str(dest/'results')
    tasks=data.tasks_for(cfg['datasets'][0],cfg['roots'])
    if len(tasks)!=len(rows):raise ValueError('Kit loader changed membership')
    prompts={t['example_id']:hashlib.sha256(official.build_prompt_context(t,'ours').encode()).hexdigest() for t in tasks}
    dump(dest/'PROMPT_PINS.json',prompts)
    for t in tasks:
        if official.infer_answer_type(t)!=t['answer_type']:raise ValueError('Kit answer type differs')
    pending=[strata(r) for r in rows if r.get('answer') is None]
    unavailable=[r for r in rows if r['stratum'] in ('missing_released','released_text_unavailable')]
    dump(dest/'request.json',cfg)
    dump(dest/'BIND_STATUS.json',dict(tasks=len(tasks),layout=cell['layout'],captures=len({r['native'] for r in rows}),
                                    dry=args.dry,missing_labels=len(pending),unavailable_released=len(unavailable),ready=False,
                                    pending=['PNG existence, byte hashes, dimensions, pixel hashes'] if args.dry else []))
    if args.dry:
        dump(dest/'RECEIPT_TEMPLATES.json',[receipt_template(t,cell,captures[t['native']],media) for t in tasks])
        print(json.dumps({'dry_bind':'PASS; stopped before PNG bytes','tasks':len(tasks),'missing_labels':len(pending),'dest':str(dest)}));return
    if pending:raise ValueError(f'{len(pending)} rows lack canonical/released labels; see LABEL_BLOCKERS and DESIGN_RECORD. No launch.')
    result=make_frames(cfg,tasks,captures,media,Path(args.frames_root),dest/'frames')
    dump(dest/'BIND_STATUS.json',dict(tasks=len(tasks),ready=True,dry=False,frames_sha256=result))
    print(json.dumps({'ready':True,'config':str(dest/'request.json')}))


def receipt_template(task,cell,capture,media):
    validate_timing(capture)
    anchors=capture['anchor_indices'];expanded,_=media.frame_list(anchors,capture['fps'],capture['total_num_frames'],cell['layout'])
    by_index={f['index']:f for f in capture['frames']}
    if [f['index'] for f in capture['frames']]!=anchors:raise ValueError('Frame plan order differs')
    frames=[by_index[i] for i in expanded]
    h,w=capture['hw']
    audit=dict(metadata=dict(fps=capture['fps'],frames_indices=expanded,total_num_frames=capture['total_num_frames'],height=h,width=w),
               anchor_indices=anchors,end_fallback_anchors=[],requested_gap=None,
               realized_gaps=[(expanded[i+1]-expanded[i])/capture['fps'] for i in range(0,len(expanded),2)],
               source_frame_indices=anchors,pixel_sha256=None,
               timestamps=[i/capture['fps'] for i in expanded],
               total_num_frames_lower_bound=capture['total_num_frames_lower_bound'],
               timing_version=TIMING_VERSION,fps_rule=capture['fps_rule'],plan_alias=capture['plan_alias'])
    return dict(identity=media.identity(task,cell['layout']),frames=frames,audit=audit)


def safe_frame(root,name):
    p=root/name
    if Path(name).is_absolute() or not p.resolve().is_relative_to(root.resolve()):raise ValueError('Frame path escapes root')
    return p


def make_frames(cfg,tasks,captures,media,frame_root,cache):
    import numpy as np
    from PIL import Image
    frame_root=frame_root.resolve();cache.mkdir(parents=True,exist_ok=False)
    # Check every required planned anchor, even captures not selected by these cells.
    required={f['path']:f['sha256'] for c in captures.values() for f in c['frames']}
    for name in required:
        if not safe_frame(frame_root,name).is_file():raise ValueError('Missing PNG: '+name)
    sample=sorted(required,key=lambda p:hashlib.sha256(('devS1-byte-sample-v1|'+p).encode()).hexdigest())[:64]
    for name in sample:
        if sha(safe_frame(frame_root,name))!=required[name]:raise ValueError('Sample PNG hash differs: '+name)
    receipts={};items={};cell=cfg['cells'][0]
    for t in tasks:
        rec=receipt_template(t,cell,captures[t['native']],media);ident=digest(rec['identity'])
        if ident not in receipts:
            arrays={}
            for pin in rec['frames']:
                name=pin['path']
                if name in arrays:continue
                src=safe_frame(frame_root,name)
                if sha(src)!=pin['sha256']:raise ValueError('PNG hash differs: '+name)
                with Image.open(src) as im:
                    if im.format!='PNG' or im.mode!='RGB':raise ValueError('Require RGB PNG')
                    arrays[name]=np.array(im)
                target=cache/name;target.parent.mkdir(parents=True,exist_ok=True)
                if not target.exists():os.link(src,target)  # Same local filesystem required; no silent bulk copy.
            stack=np.stack([arrays[p['path']] for p in rec['frames']])
            h,w=captures[t['native']]['hw']
            if list(stack.shape)!=[len(rec['frames']),h,w,3]:raise ValueError('PNG dimensions differ from PLAN')
            rec['audit']['pixel_sha256']=media.pixel_digest(stack)
            rel='receipts/'+ident+'.json';dump(cache/rel,rec);receipts[ident]=dict(path=rel,sha256=sha(cache/rel))
        items[media.item_key(t,cell['layout'])]=receipts[ident]
    dump(cache/'0.json',dict(schema=1,binding=cfg['binding'],source_sha256=cfg['source_sha256'],items=items,
                           decodes=len(receipts),errors=0,workers=1,seconds=None))
    dump(cache/'BYTE_CHECK.json',dict(all_exist=len(required),sample=sample,sample_verified=len(sample),
                                    all_used_bytes_verified=True,plan_sha256=json.loads((Path(cfg['devs1']['payload'])/'FRAMES.json').read_text())['plan_sha256']))
    return sha(cache/'0.json')


def verify_bound(dest):
    dest=Path(dest).resolve();cfg=json.loads((dest/'request.json').read_text());request={k:v for k,v in cfg.items() if k not in ('binding','output')}
    if cfg.get('devs1',{}).get('timing_version')!=TIMING_VERSION:
        raise ValueError('Old timing version is void; create a new binding')
    validate_cell(cfg['cells'][0],cfg['cells'][0]['model'])
    if hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()!=cfg['binding']:raise ValueError('Request binding differs')
    _,bound_pins,_,_=payload(cfg['devs1']['payload'])
    if bound_pins!=cfg['devs1']['pins']:raise ValueError('Frozen payload changed after bind')
    if cfg['build_only']:raise ValueError('Dry bind cannot launch')
    if sha(dest/'kit/CODE_PINS.json')!=cfg['devs1']['code_pins_sha256']:raise ValueError('Code inventory changed')
    if sha(__file__)!=cfg['devs1']['adapter_sha256']:raise ValueError('Adapter changed after bind')
    for name,h in json.loads((dest/'kit/CODE_PINS.json').read_text()).items():
        if sha(dest/'kit/evaluator'/name)!=h:raise ValueError('Copied kit changed after bind')
    if sha(dest/'kit/source.tar')!=cfg['source_sha256']:raise ValueError('Source archive changed')
    status=json.loads((dest/'BIND_STATUS.json').read_text())
    if cfg['build_only'] or not status['ready']:raise ValueError('Dry/incomplete bind cannot launch')
    if sha(dest/'frames/0.json')!=status['frames_sha256']:raise ValueError('Frame index changed')
    return dest,cfg,status


def launch(args):
    import asyncio
    from types import SimpleNamespace
    dest,cfg,status=verify_bound(args.dest);kit_import(dest/'kit')
    devices=os.environ.get('CUDA_VISIBLE_DEVICES','').split(',')
    if len(devices)!=1 or not devices[0]:raise ValueError('Set exactly one CUDA_VISIBLE_DEVICES card')
    if importlib.import_module('vllm').__version__!=cfg['engine_version']:raise ValueError('vLLM version differs')
    stage=importlib.import_module('stage');model=cfg['cells'][0]['model']
    base=stage.prepare(cfg['models']['base'],None,dest/'models/base')
    path=stage.prepare(cfg['models'][model],base,dest/'models'/model)
    worker=importlib.import_module('worker')
    a=SimpleNamespace(config=str(dest/'request.json'),model=str(path),cell=0,cache=str(dest/'frames'),
                      frames_sha256=status['frames_sha256'],rank=0,world=1,attempt=args.attempt,budget_only=False)
    asyncio.run(worker.run(a))
    importlib.import_module('merge').merge(cfg,0,args.attempt)
    if model=='cp1m200':importlib.import_module('budget_merge').merge_budgets(cfg,0,args.attempt)


def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='command',required=True)
    q=sp.add_parser('bind');q.add_argument('--payload',default=str(Path(__file__).parent))
    for n in ('kit','dest','models','frames-root'):q.add_argument('--'+n,required=True)
    q.add_argument('--cell',choices=['cp1m200','f17'],required=True);q.add_argument('--dry',action='store_true')
    q=sp.add_parser('launch');q.add_argument('--dest',required=True);q.add_argument('--attempt',required=True)
    a=p.parse_args();(bind if a.command=='bind' else launch)(a)
if __name__=='__main__':main()
