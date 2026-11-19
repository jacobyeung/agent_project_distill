"""Vehicle-P family coverage over the actual admitted sampler populations."""
import math

ROUTING = ('camera_displacement', 'camera_movement_direction', 'camera_rotation', 'absolute_distance')
UNITS = ('cm', 'ft', 'in')

def unit_name(row):
    raw=row.get('routing',row)
    value=raw.get('ground_record',{}).get('unit')
    names={'cm':'cm','centimeter':'cm','centimeters':'cm','centimetre':'cm','centimetres':'cm',
           'ft':'ft','foot':'ft','feet':'ft','in':'in','inch':'in','inches':'in'}
    if value not in names:raise ValueError('Unknown unit: '+str(value))
    return names[value]

def absent_on_p(cfg, unit_counts=None):
    cells=cfg['type_mix']['streams']['vqa']['cells']
    result=[dict(family='recovery',reason='Sealed ground_rows.py refuses not_seen; recovery joins vehicle N.')]
    if not cells['room']['cents']:
        result.append(dict(family='room',reason='Room launch dose is zero.'))
    if not cells['size']['cents']:
        result.append(dict(family='size',reason='Size launch dose is zero; stored size rows are not drawn.'))
    if not cfg['type_mix'].get('unit_rows'):
        result.append(dict(family='units',reason='No faithful unit file is bound; launch dose is zero.'))
    elif unit_counts is not None:
        for unit in UNITS:
            count=unit_counts.get('by_unit',{}).get(unit,0)
            if count<100:result.append(dict(family='units/'+unit,eligible=count,reason='Fewer than 100 eligible rows.'))
    return result

def required_families(cfg, audit, *, local_selection=None):
    """Local routing presence is source-selection evidence; production uses final rows."""
    spec=cfg['type_mix'];steps=cfg['recipe']['steps'];missing=[];checked={};unmeasured=[]
    tables=audit['tables'];pop=audit['eligible_by_family']
    required={'vqa':[n for n,c in spec['streams']['vqa']['cells'].items() if c['cents']], 'routing':list(ROUTING)}
    if spec.get('unit_rows') and tables.get('routing',{}).get('units',{}).get('final_cents',spec['streams']['routing']['cells']['units']['cents']):required['routing'].append('units')
    for stream,names in required.items():
        for name in names:
            item=tables.get(stream,{}).get(name,{})
            count=pop.get(stream,{}).get(name,0)
            if stream=='routing' and local_selection is not None:
                # Camera programs come from the pinned legacy routing stream, not the pool.
                # An unavailable local database is not evidence of a zero population.
                if name in ROUTING[:3] and stream not in pop:
                    present=spec['streams'][stream]['cells'].get(name,{}).get('cents',0)>0 and cfg.get('streams',{}).get('routing') and cfg.get('route_table',{}).get(name)=='route'
                    checked[stream+'/'+name]=dict(status='NOT_RUN' if present else 'FAIL',eligible=None,
                        source=cfg.get('streams',{}).get('routing'),reason='Legacy routing population is unavailable locally.')
                    (unmeasured if present else missing).append(stream+'/'+name)
                    continue
                aliases={'absolute_distance':('object_abs_distance','absolute_distance_object')}
                count=sum(sum(e.get('per_type',{}).get(t,0) for t in aliases.get(name,(name,)))
                          for e in local_selection['sources'].values() if e['status']=='ELIGIBLE') if name!='units' else audit.get('unit_counts',{}).get('sampling_eligible',0)
            cents=item.get('final_cents',spec['streams'][stream]['cells'][name]['cents'])
            draws=math.ceil(cents*steps/100)
            ok=count>0 and count*4>=draws and cents>0
            checked[stream+'/'+name]=dict(eligible=count,capped_draw=draws,repeat_cap=4,status='PASS' if ok else 'FAIL')
            if not ok:missing.append(stream+'/'+name)
    unit_counts=audit.get('unit_counts',{}).get('by_unit',{})
    missing_units=[u for u in UNITS if unit_counts.get(u,0)<100] if spec.get('unit_rows') else []
    return dict(status='FAIL' if missing else 'NOT_RUN' if unmeasured else 'PASS',vehicle='P',required=required,checked=checked,
                missing=missing,unmeasured=unmeasured,missing_units=missing_units,absent_on_P=absent_on_p(cfg,audit.get('unit_counts',{})),
                units_bound=bool(spec.get('unit_rows')),
                scope='Post-filter VQA and native source-selection routing presence; final routing counts require production proof.' if local_selection is not None else 'All post-filter staged populations and capped draws over the planned schedule.')
