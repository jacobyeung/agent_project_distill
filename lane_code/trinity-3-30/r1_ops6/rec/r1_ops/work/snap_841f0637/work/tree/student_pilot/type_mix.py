"""Opt-in quotas over admitted rows; absent policy preserves the sealed sampler."""
from collections import Counter
import hashlib
from pathlib import Path
import random
import re
import sqlite3
import json
from .p3_provenance import file_pin, load, pinned, write

RELATIVE = ('camera_obj_rel_dist_v1','camera_obj_rel_dist_v2','camera_obj_rel_dist_v3',
            'obj_obj_relative_pos_lr','obj_obj_relative_pos_nf','obj_obj_relative_pos_ud')


def room_trace(row):
    text=row.get('target','');lines=text.splitlines()
    locate=[i for i,s in enumerate(lines) if re.match(r'^Locate\b',s)]
    relate=[i for i,s in enumerate(lines) if re.match(r'^Relate\b',s)]
    estimate=[i for i,s in enumerate(lines) if re.match(r'^(?:Estimate\b|I estimate\b)',s)]
    frames=row.get('student_input',{}).get('frames',[])
    if not locate or len(relate)!=1 or not estimate or not max(locate)<relate[0]<min(estimate):return False
    for i in locate:
        cites=re.findall(r'\bframe\s+(\d+)\b',lines[i],re.I)
        if not cites or any(not 1<=int(n)<=len(frames) for n in cites):return False
        if any(not isinstance(frames[int(n)-1],dict) or not frames[int(n)-1].get('path') or
               not re.fullmatch('[0-9a-f]{64}',frames[int(n)-1].get('sha256','')) for n in cites):return False
    return True


def family(row,stream,size_selector=None):
    raw=row.get('routing',row);typ=raw.get('question_type',row.get('question_type'))
    if stream=='routing':
        record=raw.get('ground_record',{})
        qid=str(row.get('qid',raw.get('qid','')))
        if record.get('not_seen') or qid.startswith('a0_recovery_'):return 'recovery'
        if record.get('unit') or qid.startswith('a0_units_'):return 'units'
        return {'camera_displacement':'camera_displacement','camera_movement_direction':'camera_movement_direction',
                'camera_rotation':'camera_rotation','object_abs_distance':'absolute_distance',
                'absolute_distance_object':'absolute_distance'}.get(typ,'excluded_routing_type')
    if stream!='vqa':return stream
    if typ in RELATIVE:return typ
    if typ in ('room_size_estimation','absolute_size_room'):return 'room' if room_trace(row) else 'excluded_room_trace'
    if typ in ('object_size_estimation','absolute_size_object','relative_size_object'):
        if size_selector:
            value=row
            for key in size_selector['field'].split('.'):
                value=value.get(key) if isinstance(value,dict) else None
            if value!=size_selector['equals']:return 'excluded_size_selector'
        return 'size'
    if typ in ('object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard',
               'relative_direction_object','absolute_direction_object'):
        return 'facing' if row.get('facing') in ('toward','away') else 'direction'
    if typ in ('object_counting','absolute_count','relative_count'):
        return 'totals' if row.get('count_kind')=='total' else 'counting'
    return {'object_rel_distance':'relative_distance','relative_distance_object':'relative_distance',
            'obj_appearance_order':'appearance','appearance_order':'appearance','first_seen_frame':'first_seen',
            'box_3d':'box','route_planning':'route','camera_obj_abs_dist':'camera_absolute_distance',
            'camera_obj_rel_dist':'relative_distance'}.get(typ,'unassigned:'+str(typ))


def validate(spec,recipe):
    if not isinstance(spec,dict) or set(spec)-{'schema','streams','max_repeats','size_selector','vehicle','unit_rows'} or not {'schema','streams','max_repeats','size_selector'}<=set(spec) or spec['schema']!='type-mix-v2':
        raise ValueError('Invalid type mix')
    if 'vehicle' in spec:
        if spec['vehicle']!='P':raise ValueError('Unknown vehicle family policy')
        routing=spec['streams'].get('routing',{})
        cells=routing.get('cells',{})
        if cells.get('recovery',{}).get('cents',0) or 'recovery' in routing.get('refill',[]):
            raise ValueError('Recovery is absent on vehicle P')
        if not spec.get('unit_rows') and (cells.get('units',{}).get('cents',0) or 'units' in routing.get('refill',[])):
            raise ValueError('Units are refused when unbound')
        unit=spec.get('unit_rows')
        if unit is not None and (set(unit)!={'path','sha256'} or not re.fullmatch('[0-9a-f]{64}',unit['sha256'])):
            raise ValueError('Unit rows require an exact file pin')
    if spec['max_repeats']!=4 or type(spec['max_repeats']) is not int:raise ValueError('Repeat cap must be four')
    selector=spec['size_selector']
    if selector is not None and (not isinstance(selector,dict) or set(selector)!={'field','equals'} or
            not isinstance(selector['field'],str) or not selector['field']):raise ValueError('Invalid size selector')
    if set(spec['streams'])-{'vqa','routing'}:raise ValueError('Unsupported quota stream')
    slots=Counter(recipe['mix'])
    for stream,policy in spec['streams'].items():
        if set(policy)-{'cells','refill','refill_mode'} or not {'cells','refill'}<=set(policy) or not isinstance(policy['refill'],list):raise ValueError('Invalid refill policy')
        if policy.get('refill_mode','ordered') not in ('ordered','proportional'):raise ValueError('Invalid refill mode')
        cells=policy['cells']
        if set(policy['refill'])-set(cells) or len(policy['refill'])!=len(set(policy['refill'])):raise ValueError('Unknown refill family')
        if not cells:raise ValueError('Empty quota stream')
        for name,c in cells.items():
            if not re.fullmatch('[a-z0-9_]+',name) or set(c)!={'cents'} or type(c['cents']) is not int or c['cents']<0:
                raise ValueError('Invalid family quota')
        if sum(c['cents'] for c in cells.values())!=slots[stream]*recipe['world_size']*100:
            raise ValueError('Family quotas must fill the unchanged stream batch')
    return spec


def allocate(policy,counts,steps,max_repeats=4):
    cells=policy['cells'];total=sum(c['cents'] for c in cells.values());table={}
    for name,cell in cells.items():
        eligible=counts.get(name,0);cap=eligible*max_repeats*100//steps
        capped=min(cell['cents'],cap)
        table[name]=dict(eligible=eligible,proposed_cents=cell['cents'],cap_cents=cap,
                         capped_cents=capped,cut_cents=cell['cents']-capped,refill_cents=0,final_cents=capped)
    deficit=total-sum(v['final_cents'] for v in table.values())
    if policy.get('refill_mode','ordered')=='proportional':
        while deficit:
            active=[n for n in policy['refill'] if cells[n]['cents']>0 and table[n]['final_cents']<table[n]['cap_cents']]
            if not active:break
            total_weight=sum(cells[n]['cents'] for n in active);amount=deficit
            for name in active:
                item=table[name];extra=min(item['cap_cents']-item['final_cents'],amount*cells[name]['cents']//total_weight)
                item['refill_cents']+=extra;item['final_cents']+=extra;deficit-=extra
            # Largest remainders resolve fractional cents deterministically.
            for name in sorted(active,key=lambda n:(-(amount*cells[n]['cents']%total_weight),n)):
                item=table[name]
                if deficit and item['final_cents']<item['cap_cents']:
                    item['refill_cents']+=1;item['final_cents']+=1;deficit-=1
    else:
        for name in policy['refill']:
            item=table[name];extra=min(deficit,item['cap_cents']-item['final_cents'])
            item['refill_cents']=extra;item['final_cents']+=extra;deficit-=extra
    if deficit:raise ValueError('Insufficient eligible rows to fill capped stream: '+str(deficit))
    effective={n:dict(cents=v['final_cents']) for n,v in table.items() if v['final_cents']}
    return effective,table


def populations(stream,source,cells,size_selector=None,unit_rows=None):
    indices=load(pinned(source['indices'])) if 'indices' in source else list(range(source['count']))
    positions={i:j for j,i in enumerate(indices)}
    if len(positions)!=len(indices):raise ValueError('Duplicate admitted indices')
    buckets={name:[] for name in cells};types={};samples={};excluded=Counter();seen=set()
    db=Path(pinned(source['database']))
    conn=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        for i,encoded in conn.execute('SELECT i,row FROM rows ORDER BY i'):
            if i not in positions:continue
            seen.add(i);row=json.loads(encoded);name=family(row,stream,size_selector)
            if name.startswith('excluded_'):excluded[name+':'+str(row.get('routing',row).get('question_type'))]+=1;continue
            if stream=='routing' and name=='units' and unit_rows is not None and row.get('s1_source',{}).get('source',{}).get('sha256')!=unit_rows['sha256']:
                raise ValueError('Unit row is outside the bound source')
            if name not in cells:raise ValueError('Eligible family lacks a quota: '+stream+'/'+name)
            pos=positions[i];buckets[name].append(pos)
            types[pos]=row.get('routing',row).get('question_type')
            if len(samples.setdefault(name,[]))<5:
                samples[name].append(dict(index=i,position=pos,qid=row['qid'],question_type=types[pos],
                    target=row['target'],target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
                    frames=row.get('student_input',{}).get('frames',[])))
    finally:conn.close()
    if seen!=set(indices):raise ValueError('Admitted indices missing from database')
    return buckets,types,samples,dict(excluded)


def prepare(receipt,cfg):
    spec=cfg.get('type_mix')
    if spec is None:return receipt
    validate(spec,cfg['recipe']);groups={};effective={};tables={}
    for stream,policy in spec['streams'].items():
        cells=policy['cells']
        src=receipt['streams'][stream]
        if src.get('kind') in ('mix','mdg'):raise ValueError('Quotas require a flat admitted stream')
        buckets,_,_,_=populations(stream,src,cells,spec['size_selector'],spec.get('unit_rows'))
        chosen,table=allocate(policy,{n:len(ids) for n,ids in buckets.items()},cfg['recipe']['steps'],spec['max_repeats'])
        effective[stream]=chosen;tables[stream]=table
        buckets={n:buckets[n] for n in chosen}
        for name,ids in buckets.items():
            if not ids:raise ValueError('Required quota family is empty: '+stream+'/'+name)
            draws=(cfg['recipe']['steps']*chosen[name]['cents']+99)//100
            if draws>len(ids)*spec['max_repeats']:raise ValueError('Quota exceeds repeat cap: '+stream+'/'+name)
        groups[stream]=buckets
    value=dict(schema='type-mix-populations-v2',spec=spec,recipe=cfg['recipe'],
        streams={s:receipt['streams'][s] for s in groups},populations=groups,effective=effective,tables=tables)
    path=Path(cfg['preparation_output'])/'type_mix.json';write(path,value)
    return {**receipt,'type_mix':spec,'type_mix_population':file_pin(path)}


def bound(receipt,cfg):
    spec=cfg.get('type_mix')
    if receipt.get('type_mix')!=spec:raise ValueError('Prepared mix differs')
    if spec is None:return None
    value=load(pinned(receipt['type_mix_population']))
    validate(spec,cfg.get('recipe',value['recipe']))
    if 'recipe' in cfg and value['recipe']!=cfg['recipe']:raise ValueError('Prepared schedule differs')
    if value['spec']!=spec:raise ValueError('Population policy differs')
    if value['streams']!={s:receipt['streams'][s] for s in spec['streams']}:raise ValueError('Population admission differs')
    for stream,policy in spec['streams'].items():
        counts={n:v['eligible'] for n,v in value['tables'][stream].items()}
        actual,table=allocate(policy,counts,value['recipe']['steps'],spec['max_repeats'])
        if actual!=value['effective'][stream] or table!=value['tables'][stream]:raise ValueError('Capped quota differs')
        if {n:len(ids) for n,ids in value['populations'][stream].items()}!={n:counts[n] for n in actual}:raise ValueError('Capped population count differs')
    return value


def plans(base,value,seed,start_step=0):
    """Deterministic weighted round robin; resume replays the same shuffled epochs."""
    spec=value['spec'];cells=value['effective'];groups=value['populations']
    rngs={};orders={};cursors={};credits={};draws=Counter()
    for stream in cells:
        if set(cells[stream])!=set(groups[stream]):raise ValueError('Quota population families differ')
        flat=[i for ids in groups[stream].values() for i in ids]
        if len(flat)!=len(set(flat)):raise ValueError('Quota populations overlap')
        credits[stream]=dict.fromkeys(cells[stream],0)
        for name in cells[stream]:
            key=(stream,name);orders[key]=list(groups[stream][name])
            if not orders[key]:raise ValueError('Empty quota population')
            salt=int.from_bytes(hashlib.sha256((stream+'/'+name).encode()).digest()[:8],'big')
            rngs[key]=random.Random(seed+salt);rngs[key].shuffle(orders[key]);cursors[key]=0
    for step,plan in enumerate(base):
        result=[]
        for stream,indices in plan:
            if stream not in cells:result.append((stream,indices));continue
            chosen=[];total=sum(v['cents'] for v in cells[stream].values())
            for _ in indices:
                for name,v in cells[stream].items():credits[stream][name]+=v['cents']
                name=max(sorted(cells[stream]),key=lambda n:credits[stream][n]);credits[stream][name]-=total;key=(stream,name)
                if cursors[key]==len(orders[key]):rngs[key].shuffle(orders[key]);cursors[key]=0
                index=orders[key][cursors[key]];cursors[key]+=1;draws[stream,index]+=1
                if draws[stream,index]>spec['max_repeats']:raise ValueError('Repeat cap exceeded')
                chosen.append(index)
            result.append((stream,chosen))
        if step>=start_step:yield result
