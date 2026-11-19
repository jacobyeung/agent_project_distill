"""Pinned wording exclusion and coverage-source identities for training intake."""
import json,re,unicodedata
from .p3_provenance import load,pinned,digest

SPLIT = '2463193d00fabda5c62d07027527f57a5943dd52ee2b346a215576e55d1abf19'
PINS = {'coverage_units':'8ec1efd2c1851fb856caa3631653390d76796f8c31cd8366d54df52916c7de82',
        'coverage_distance':'15387646fd4ac47b43c107129db3109545a981c1bd45a3910ac038d8c5432022'}

def source_names(sources):
    from .r1_population import SLICE_CELLS
    extra=set(sources)&set(PINS)
    if extra and extra!=set(PINS):raise ValueError('R1_COVERAGE_SOURCES_INCOMPLETE')
    return (*SLICE_CELLS,*sorted(extra))

def normalize(text):
    return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())

class WordingExclusion:
    def __init__(self,pin):
        if pin.get('sha256')!=SPLIT:raise ValueError('R1_WORDING_EXCLUSION_PIN')
        value=load(pinned(pin));self.patterns=[]
        if len(value.get('held_out',[]))!=8:raise ValueError('R1_WORDING_EXCLUSION_COUNT')
        for template in value['held_out']:
            expression=re.escape(normalize(template))
            for name in ('a','b','u'):expression=expression.replace(re.escape('{'+name+'}'),'.+?')
            self.patterns.append((template,re.compile('^'+expression+'$')))

    def check(self,row):
        for value in (row,row.get('student_input',{}),row.get('routing',{}),row.get('ground_record',{})):
            if not isinstance(value,dict):continue
            question=value.get('question')
            if isinstance(question,str):
                for name,pattern in self.patterns:
                    if pattern.fullmatch(normalize(question)):
                        raise ValueError('R1_HELD_OUT_WORDING:'+name)
        return row

def validate_binding(cfg):
    value=cfg.get('r1_training') or {};pin=value.get('wording_exclusion')
    sources=load(pinned(value['row_sources'])) if value.get('row_sources') else {}
    extra=set(PINS)&set(sources)
    if extra:
        source_names(sources)
        if pin is None:raise ValueError('R1_WORDING_EXCLUSION_REQUIRED')
        for name,h in PINS.items():
            if sources[name]['source']['sha256']!=h:raise ValueError('R1_COVERAGE_SOURCE_PIN:'+name)
            pinned(sources[name]['source'])
    return WordingExclusion(pin) if pin else None

def rewording(child,parent):
    """Prove that a pinned coverage row changes wording and identifiers only."""
    from copy import deepcopy
    a,b=deepcopy(child),deepcopy(parent)
    units='ground_record' in a
    p=a['provenance']
    edit=p.get('details',{}).pop('question_edit',None) if units else p.pop('dist_diag_question_edit',None)
    if (not edit or edit.get('reworded_from')!=b['qid'] or edit.get('before')!=b['question']
            or edit.get('after')!=a['question'] or edit.get('candidate_id_before')!=b['candidate_id']
            or False):raise ValueError('R1_COVERAGE_PARENT_IDENTITY')
    keys=('qid','question','candidate_id') if units else ('qid','question','question_identity','candidate_id')
    for row in (a,b):
        for key in keys:row.pop(key,None)
        if units:
            for key in ('qid','question','question_identity','candidate_id'):row['ground_record'].pop(key,None)
    if a!=b:raise ValueError('R1_COVERAGE_NON_WORDING_CHANGE')
    return parent['qid']

def union_rows(base,extra):
    values={}
    for rows in (base,extra):
        for row in rows:
            if (set(row)!={'row_key','canonical','reason'} or row.get('reason')!='k1_heldout_v7'
                    or not isinstance(row.get('row_key'),str) or not row['row_key']
                    or not isinstance(row.get('canonical'),str) or '/' not in row['canonical']):
                raise ValueError('R1_K1_UNION_ROW_INVALID')
            if row['row_key'] in values and values[row['row_key']]!=row:raise ValueError('R1_K1_UNION_CONFLICT')
            values[row['row_key']]=row
    return [values[k] for k in sorted(values)]

def read_list(pin):
    with pinned(pin).open() as f:return [json.loads(line) for line in f if line.strip()]

def verify_union(value,removals,base_hash,n_hash):
    spec=value.get('v7_k1_union');pin=value.get('v7_k1_removal',{})
    if not spec:return False
    if set(spec)!={'base','extra','union'} or spec['base'].get('sha256')!=base_hash or spec['union']!=pin:
        raise ValueError('R1_K1_UNION_BINDING')
    expected=union_rows(read_list(spec['base']),read_list(spec['extra']))
    if read_list(pin)!=expected:raise ValueError('R1_K1_UNION_CONTENT')
    hashes=[p['sha256'] for p in removals]
    if (hashes.count(base_hash)!=1 or hashes.count(pin['sha256'])!=1 or n_hash not in hashes
            or not hashes.index(base_hash)<hashes.index(pin['sha256'])<hashes.index(n_hash)):
        raise ValueError('R1_K1_UNION_ORDER')
    return True
