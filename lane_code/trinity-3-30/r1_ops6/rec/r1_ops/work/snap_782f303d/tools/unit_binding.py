"""Add an immutable packed unit source using the sealed native pool admission."""
import copy,gzip,hashlib,json,re,tempfile
from collections import Counter
from pathlib import Path

NAME='U_Faithful'
AS='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/'
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(enc(v)+'\n')
def pin(p):return dict(path=str(p),sha256=sha(p))

def pack_slice(rows, expected, authority, expected_authority, parent, out):
    """Reconstruct only omitted events and frame inputs; preserve the supplied payload."""
    from student_pilot import ground_rows,s1_pool,s1_routing
    rows=Path(rows);out=Path(out)
    if sha(rows)!=expected:raise ValueError('Unit slice SHA differs')
    if set(authority)!={'frame_map','frame_plan','fps_authority'}:raise ValueError('Unit packing requires map, plan and FPS authority')
    actual=s1_pool.implementation()
    for name in ('student_pilot/ground_rows.py','student_pilot/s1_pool.py','student_pilot/s1_routing.py'):
        if actual.get(name)!=parent['implementation'].get(name):raise ValueError('Unit packing predicate differs: '+name)
    for key,value in authority.items():
        if set(value)!={'path','sha256'} or value['sha256']!=expected_authority[key]['sha256'] or sha(value['path'])!=value['sha256']:
            raise ValueError('Unit frame authority differs: '+key)
    frames=s1_routing.Frames(authority['frame_map'],authority['frame_plan'],fps_authority=authority['fps_authority'])
    output=[];qids=set()
    for line in rows.read_bytes().splitlines():
        row=json.loads(line)
        if 'events' in row:raise ValueError('Slice packing requires omitted top-level events')
        envelope=ground_rows.pack(dict(row['ground_record'],suffix=row['target']),row['provenance'])
        # source_qid remains the original source join, not pack()'s duplicate of qid.
        for key,value in envelope.items():
            if key in row and key!='source_qid' and row[key]!=value:
                raise ValueError('Native unit packing would change supplied payload: '+key)
        packed=copy.deepcopy(row);packed['events']=envelope['events']
        request=s1_routing.frame_request(packed)
        for value in (row.get('frame_indices'),row['ground_record'].get('frame_indices')):
            if value is not None and value!=request['i']:raise ValueError('Unit slice frame indices differ')
        inputs,_=frames.resolve(packed)
        packed['student_input']=inputs
        s1_pool.validate_source_row(packed,'packed')
        if packed['qid'] in qids:raise ValueError('Duplicate unit QID')
        qids.add(packed['qid']);output.append(enc(packed)+'\n')
    raw=''.join(output).encode();counts=inspect_rows(raw)
    out.parent.mkdir(parents=True,exist_ok=True,mode=0o700);out.write_bytes(raw)
    return dict(schema='unit-slice-packing-v1',slice=pin(rows),packed=pin(out),frame_authority=authority,
        implementation={n:actual[n] for n in ('student_pilot/ground_rows.py','student_pilot/s1_pool.py','student_pilot/s1_routing.py')},
        rows=counts['eligible'],payload_changed=False,source_qid_preserved=True,
        additions=['events','student_input frame pins and native timing fields'],rgb_bytes_verified=False)


def inspect_rows(raw):
    from student_pilot import s1_pool,s1_routing
    from student_pilot.vehicle_p import unit_name,UNITS
    counts=Counter();datasets=Counter();cross=Counter();qids=set()
    for line in raw.splitlines():
        row=json.loads(line)
        if 'events' not in row:raise ValueError('Unit rows require top-level events and all 32 explicit frame pins')
        s1_pool.validate_source_row(row,'packed')
        if row['question_type']!='object_abs_distance':raise ValueError('Unit source must contain absolute-distance programs')
        if row['qid'] in qids:raise ValueError('Duplicate unit QID')
        qids.add(row['qid'])
        frames=row.get('student_input',{}).get('frames')
        if not isinstance(frames,list) or len(frames)!=32 or any(set(p)!={'path','sha256'} or not p['path'] or not re.fullmatch('[0-9a-f]{64}',p['sha256']) for p in frames):
            raise ValueError('Unit rows require all 32 explicit frame pins')
        s1_routing.frame_request(row)
        unit=unit_name(row);dataset=row.get('dataset',row['provenance']['canonical'].split('/')[0])
        counts[unit]+=1;datasets[dataset]+=1;cross[unit+'/'+dataset]+=1
    if not qids:raise ValueError('Empty unit source')
    return dict(eligible=len(qids),by_unit={u:counts[u] for u in UNITS},by_dataset=dict(datasets),by_unit_dataset=dict(cross),
                missing_units=[u for u in UNITS if counts[u]<100])

def native_source(parent,source,metadata,resolve,directory,logical_index):
    """Execute sealed admission; pin relocation changes no row or predicate."""
    from student_pilot import s1_pool
    actual=s1_pool.implementation()
    for name in ('ground_rows.py','s1_pool.py','s1_exclusions.py','s1_scene_census.py','row_removals.py'):
        key='student_pilot/'+name
        if actual.get(key)!=parent['implementation'].get(key):raise ValueError('Unit admission predicate differs: '+name)
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    empty=directory/'e.tsv';empty.write_text('')
    scenes={k:pin(resolve(v)) for k,v in parent['scene_exclusions'].items()}
    removals=[{**v,'path':str(resolve(v))} for v in parent['remove_files']]
    manifest=dict(schema='dose-pool-s1-manifest-v2',sets=[dict(name=NAME,status='final',
        files={'packed':dict(**pin(resolve(source)),rows=metadata['eligible'])},
        rows_per_type={'object_abs_distance':metadata['eligible']})],exclusions={
        'dev_s1':dict(list=str(empty),list_sha256=sha(empty),rows=0,withhold=scenes['dev']['path'],withhold_sha256=scenes['dev']['sha256']),
        'eval_rooms':dict(list=str(empty),list_sha256=sha(empty),rows=0,v2=scenes['benchmark']['path'],v2_sha256=scenes['benchmark']['sha256']),
        'room_release_gate':dict(list=str(empty),list_sha256=sha(empty),rows=0)})
    write(directory/'m.json',manifest)
    report=s1_pool.prepare(pin(directory/'m.json'),directory/'native',remove_files=removals,tokenizer=None)
    entry=report['sources'][NAME]
    if entry['status']!='ELIGIBLE' or entry['retained']!=metadata['eligible'] or report['blockers']:
        raise ValueError('Unit input is not entirely admitted unchanged: '+str(entry.get('reason')))
    actual=load(entry['selection']['path'])
    if actual!=list(range(metadata['eligible'])):raise ValueError('Unit admission changed membership')
    if sha(entry['selection']['path'])!=logical_index['sha256']:raise ValueError('Native unit indices differ')
    # Map paths back to the canonical parent pins; hashes and native counts stay exact.
    entry['source']=source;entry['selection']=logical_index
    for item,original in zip(entry['removals'],parent['remove_files'],strict=True):item['file']=original
    census=report['source_scene_exclusions']
    census['files']=parent['scene_exclusions']
    expected=census['expected'][NAME]
    expected.update(files=parent['scene_exclusions'],membership_files=parent['exclusions'],source=source)
    return entry,census

def merge(parent,manifest,entry,census,manifest_pin):
    candidate=copy.deepcopy(parent)
    if NAME in candidate['sources'] or any(v['name']==NAME for v in manifest['sets']):raise ValueError('Unit source already exists')
    candidate['manifest']=manifest_pin;candidate['sources'][NAME]=entry
    for key in ('sources','datasets','expected','comparisons'):
        candidate['source_scene_exclusions'][key].update(census[key])
    candidate['declared_rows']+=entry['declared_rows'];candidate['selected_rows']+=entry['retained']
    return candidate

def build(rows,expected,parent,manifest,catalog,indices,out):
    rows=Path(rows);out=Path(out);out.mkdir(parents=True,exist_ok=True,mode=0o700)
    if sha(rows)!=expected:raise ValueError('Unit rows SHA differs')
    raw=rows.read_bytes();metadata=inspect_rows(raw)
    # Deterministic compression preserves every byte of the supplied JSONL.
    (out/'u.gz').write_bytes(gzip.compress(raw,mtime=0))
    base=AS+'u_'+expected[:16]+'/'
    source=dict(path=base+'u.gz',sha256=sha(out/'u.gz'))
    write(out/'i.json',list(range(metadata['eligible'])))
    index=dict(path=base+'i.json',sha256=sha(out/'i.json'))
    def resolve(value):
        if value['sha256']==source['sha256']:p=out/'u.gz'
        else:
            locator=catalog.get(value['sha256'])
            if locator is None:raise ValueError('Missing unit admission input in source catalog')
            p=Path(indices)/Path(locator).name
        if sha(p)!=value['sha256']:raise ValueError('Unit admission input SHA differs')
        return p
    tmp=Path(tempfile.mkdtemp(prefix='native_',dir=out))
    entry,census=native_source(parent,source,metadata,resolve,tmp,index)
    extended=copy.deepcopy(manifest)
    extended['sets'].append(dict(name=NAME,status='final',files={'packed':dict(**source,rows=metadata['eligible'],bytes=(out/'u.gz').stat().st_size)},rows_per_type={'object_abs_distance':metadata['eligible']}))
    # Totals are descriptive, but keep them consistent with the new source.
    totals=extended.get('totals',{})
    if 'rows_in_files' in totals:totals['rows_in_files']+=metadata['eligible']
    if 'final_after_exclusions' in totals:
        totals['final_after_exclusions']['rows']+=metadata['eligible']
        types=totals['final_after_exclusions']['per_type'];types['object_abs_distance']=types.get('object_abs_distance',0)+metadata['eligible']
    write(out/'m.json',extended);mp=dict(path=base+'m.json',sha256=sha(out/'m.json'))
    candidate=merge(parent,manifest,entry,census,mp)
    result=dict(schema='faithful-unit-binding-v1',input_sha256=expected,source=source,index=index,manifest=mp,
                counts=metadata,answer_regenerated=False,admission_predicates_changed=False,
                artifacts={n:dict(path=base+n,sha256=sha(out/n)) for n in ('u.gz','i.json','m.json')})
    write(out/'u.json',result)
    return candidate,result

def regenerate(parent,binding,root,indices,catalog,directory):
    root=Path(root);source=binding['source']
    def resolve(value):
        match=next((name for name,p in binding['artifacts'].items() if p['sha256']==value['sha256']),None)
        p=root/match if match else Path(indices)/Path(catalog[value['sha256']]).name
        if sha(p)!=value['sha256']:raise ValueError('Staged unit input differs')
        return p
    raw=gzip.decompress(resolve(source).read_bytes())
    if hashlib.sha256(raw).hexdigest()!=binding['input_sha256']:raise ValueError('Unit JSONL bytes differ')
    if inspect_rows(raw)!=binding['counts']:raise ValueError('Unit census differs')
    entry,census=native_source(parent,source,binding['counts'],resolve,directory,binding['index'])
    manifest=load(resolve(binding['manifest']))
    # merge checks against the parent set names; the extended file is separately pinned.
    original={**manifest,'sets':[e for e in manifest['sets'] if e['name']!=NAME]}
    return merge(parent,original,entry,census,binding['manifest'])
