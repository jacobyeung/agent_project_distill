"""Authenticate direction twins against the pinned v7 population before admission."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json, sqlite3
from .p3_provenance import load, pinned, digest, file_pin, write

ROWS = '7b3d696d580386f9e8af3240fa142e2ad50eebb277a8718c97e2db497dcc925e'
BINDING = 'd8c3837019d29e9c8b7916a7e8b3c3d595890b6cad32c7dc72ba5f871a0a5108'
ALIASES = '7f50287bae46792d1de25b33344d62d6a6484688887c5294bdd1d1f67f76623b'
COUNT = 7971
UNION = '1c7c930d1a533a3b18b08486bc2c2a9b49086b0809492963498b369ac8be45a2'

def connect(pin):
    return sqlite3.connect(pinned(pin).as_uri()+'?mode=ro&immutable=1',uri=True)

def specifications(cfg):
    from .r1_rooms import STORE
    spec=cfg['r1_training']['direction_twins']
    union=cfg['r1_training'].get('v7_k1_removal',{})
    if union.get('sha256')!=UNION:raise ValueError('R1_TWIN_K1_UNION_REQUIRED')
    from .r1_coverage import read_list
    if len(read_list(union))!=4959:raise ValueError('R1_TWIN_K1_UNION_COUNT')
    for key,expected in (('rows',ROWS),('binding',BINDING),('aliases',ALIASES),('source_database',STORE)):
        if spec.get(key,{}).get('sha256')!=expected:raise ValueError('R1_TWIN_PIN:'+key)
        pinned(spec[key])
    return spec

class Binding:
    def __init__(self,cfg):
        from .r1_rooms import Rooms, STORE
        self.spec=specifications(cfg);self.strict=Rooms(cfg['r1_training']['room_authority'])
        aliases=load(pinned(self.spec['aliases']))
        if not aliases.get('complete') or aliases.get('conflicts') or aliases.get('quarantined_tokens'):
            raise ValueError('R1_TWIN_ROOM_AUTHORITY')
        self.tiered=deepcopy(self.strict)
        self.tiered.aliases={k:v['canonical'] for k,v in aliases['aliases'].items()}
        self.records={}
        with pinned(self.spec['binding']).open() as f:
            for line in f:
                record=json.loads(line);key=record['twin_key']
                if key in self.records:raise ValueError('R1_TWIN_DUPLICATE_BINDING')
                self.records[key]=record
        if len(self.records)!=COUNT:raise ValueError('R1_TWIN_BINDING_COUNT')
        wanted={r['source_key'] for r in self.records.values()};self.sources={};self.base_keys=set()
        db=connect(self.spec['source_database'])
        try:
            for raw, in db.execute('SELECT row FROM rows ORDER BY i'):
                row=json.loads(raw);key=row['qid']
                if key in self.base_keys:raise ValueError('R1_TWIN_SOURCE_DUPLICATE')
                self.base_keys.add(key)
                if key in wanted:
                    self.sources[key]=dict(room=self.room(row),dataset=row.get('dataset'),scene=row.get('scene'))
        finally:db.close()
        if set(self.sources)!=wanted:raise ValueError('R1_TWIN_SOURCE_ABSENT_FROM_V7')
        if set(self.records)&self.base_keys:raise ValueError('R1_TWIN_KEY_COLLISION')

    def room(self,row):
        status,canonical,_=self.strict.status(row)
        if status=='unresolved':canonical,_=self.tiered.canonical(row)
        if not canonical:raise ValueError('R1_TWIN_ROOM_UNRESOLVED')
        return self.strict.room(canonical)

    def check(self,row):
        from .row_removals import row_keys
        record=self.records.get(row.get('qid'))
        if not record or digest(row)!=record['twin_sha256']:raise ValueError('R1_TWIN_ROW_DIGEST')
        if 'facing' in row:raise ValueError('R1_TWIN_FACING_FIELD')
        source=self.sources[record['source_key']]
        if (record['source_room']!=source['room'] or self.room(row)!=source['room']
                or row.get('dataset')!=source['dataset'] or row.get('scene')!=source['scene']):
            raise ValueError('R1_TWIN_SOURCE_ROOM_DIFFERS')
        if row_keys(row)!={row['qid'],record['source_key']}:
            raise ValueError('R1_TWIN_SOURCE_REMOVAL_KEY')
        return record

    def rows(self):
        seen=set()
        with pinned(self.spec['rows']).open() as f:
            for line in f:
                row=json.loads(line);self.check(row)
                if row['qid'] in seen:raise ValueError('R1_TWIN_ROW_DUPLICATE')
                seen.add(row['qid']);yield row
        if seen!=set(self.records):raise ValueError('R1_TWIN_ROWS_INCOMPLETE')

def verify_augmented(cfg,actual):
    """The STORE exception authenticates every original and appended row."""
    value=cfg['r1_training'];spec=specifications(cfg);augmentation=value.get('direction_augmented')
    if not augmentation:raise ValueError('R1_TWIN_AUGMENTATION_REQUIRED')
    proof=load(pinned(augmentation))
    if (proof.get('schema')!='r1-direction-augmentation-v1'
            or proof.get('database')!=actual or proof.get('binding')!=spec['binding']
            or proof.get('source_database')!=spec['source_database'] or proof.get('rows')!=spec['rows']):
        raise ValueError('R1_TWIN_AUGMENTATION_BINDING')
    binding=Binding(cfg);base=connect(spec['source_database']);aug=connect(actual)
    try:
        cursor=iter(aug.execute('SELECT row,target FROM rows ORDER BY i'))
        for row in base.execute('SELECT row,target FROM rows ORDER BY i'):
            if next(cursor,None)!=row:raise ValueError('R1_TWIN_BASE_POPULATION_DIFFERS')
        for row in binding.rows():
            current=next(cursor,None)
            if current is None or json.loads(current[0])!=row or json.loads(current[1])!={}:
                raise ValueError('R1_TWIN_AUGMENTED_ROW_DIFFERS')
        if next(cursor,None) is not None:raise ValueError('R1_TWIN_AUGMENTED_EXTRA_ROW')
    finally:base.close();aug.close()
    return proof

def augment(cfg,output):
    """Produce a new store on the frame host; preserve the source database."""
    from .r1_rooms import STORE
    spec=specifications(cfg);receipt=load(pinned(cfg['streams']['vqa']))
    if receipt['database']['sha256']!=STORE:raise ValueError('R1_TWIN_BASE_STORE_REQUIRED')
    binding=Binding(cfg);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    path=output/'rows.sqlite'
    if path.exists():raise ValueError('R1_TWIN_OUTPUT_EXISTS')
    source=connect(spec['source_database']);target=sqlite3.connect(path)
    count=0
    try:
        target.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT NOT NULL,target TEXT NOT NULL)')
        for raw,labels in source.execute('SELECT row,target FROM rows ORDER BY i'):
            target.execute('INSERT INTO rows VALUES(?,?,?)',(count,raw,labels));count+=1
        for row in binding.rows():
            target.execute('INSERT INTO rows VALUES(?,?,?)',(count,json.dumps(row,sort_keys=True,separators=(',',':')),'{}'));count+=1
        target.commit()
    finally:source.close();target.close()
    database=file_pin(path)
    write(output/'augmentation.json',dict(schema='r1-direction-augmentation-v1',database=database,
        binding=spec['binding'],source_database=spec['source_database'],rows=spec['rows'],count=count))
    receipt.update(database=database,count=count,source_receipt=cfg['streams']['vqa'])
    write(output/'receipt.json',receipt)
    cfg=deepcopy(cfg);cfg['streams']['vqa']=file_pin(output/'receipt.json')
    cfg['r1_training']['direction_augmented']=file_pin(output/'augmentation.json')
    verify_augmented(cfg,database)
    return cfg

def dimensions(row):
    """Report answer shares; these labels never control training selection."""
    import re
    p=row.get('provenance',{}).get('sb_rowD7',{})
    question=row.get('student_input',{}).get('question',row.get('question',''))
    wording=p.get('clause_edit',{}).get('new_clause',question)
    verb=r'\b(?:fac(?:e|ing)|look(?:ing)?)\b'
    clause='away' if re.search(verb+r'\s+away\b',wording,re.I) else 'toward' if re.search(verb,wording,re.I) else 'unspecified'
    difficulty=str(row.get('question_type',row.get('category','unknown'))).rsplit('_',1)[-1]
    label=p.get('mapped_label')
    if label is None:
        answer=str(row.get('answer',''));options=row.get('student_input',{}).get('options',[])
        if isinstance(options,dict):label=options.get(answer,'')
        elif isinstance(options,list):
            label=next((x for x in options if isinstance(x,str) and x.startswith(answer+'.')),answer)
        else:label=answer
    label=str(label).casefold()
    side='front' if 'front' in label else 'back' if 'back' in label or 'behind' in label else 'other'
    return clause,difficulty,side
