"""Audit and rebuild VSTI direct rows from hash-pinned local GT, on CPU."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import collections
import copy
import ctypes
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import re
import sqlite3
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from stage_inputs import sha

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
STORE=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
ORIGINAL_CODE=Path('/scratch/jjyeung/n30_mirror/rows_a2/v4/vsti/code')
CONFIG=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/inputs/config.json')
N=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/n.json')
SEED=20261119
THRESHOLD=.05
FAMILIES=['camera_obj_rel_dist_v1','camera_obj_rel_dist_v2','camera_obj_rel_dist_v3',
          'obj_obj_relative_pos_lr','obj_obj_relative_pos_nf','obj_obj_relative_pos_ud']
EXPECTED=dict(zip(FAMILIES,[1951,1983,1998,1998,2000,1996]))
sys.path.insert(0,str(TREE))
sys.path.insert(0,str(ORIGINAL_CODE))
import geometry as reference
from student_pilot import trace_grammar, r2_grammar
from student_pilot.carrier_c1_routing import direct_row
from student_pilot.r1_training import row_check
from student_pilot.r1_rooms import Rooms
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity

def dump(path,data):
    path.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')


def canonical_bytes(data):return json.dumps(data,sort_keys=True,separators=(',',':')).encode()


def dh(data):return hashlib.sha256(canonical_bytes(data)).hexdigest()


def normalize(text):return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())


def load_rows():
    con=sqlite3.connect('file:'+str(STORE/'vqa/rows.sqlite')+'?mode=ro',uri=True)
    ranges=json.loads((STORE/'FAMILY_INDEX_RANGES.json').read_text())['families']
    discovered={k for k in ranges if k.startswith(('camera_obj_rel_dist','obj_obj_relative_pos'))}
    assert discovered==set(FAMILIES), discovered
    rows=[]
    for family in FAMILIES:
        for a,b in ranges[family]:
            rows.extend(json.loads(s) for s, in con.execute('SELECT row FROM rows WHERE i BETWEEN ? AND ? ORDER BY i',(a,b)))
    assert dict(collections.Counter(r['question_type'] for r in rows))==EXPECTED
    assert con.execute('SELECT COUNT(*) FROM rows').fetchone()[0]==204413
    con.close()
    return rows


def room_authorities(pins):
    cfg=json.loads(CONFIG.read_text())
    authorities=cfg['r1_training']['room_authority']
    for v in authorities.values():
        assert sha(v['path'])==v['sha256'];pins[v['path']]=v['sha256']
    rooms=Rooms(authorities)
    paths={'withheld80':TREE/'student_pilot/r2_withheld.json',
           'dev_s1':ROOT/'inputs/dev_scene_exclusions.json',
           'benchmark':Path(cfg['benchmark_scene_exclusions']['path'])}
    expected={'withheld80':'634820b4','dev_s1':'969cdb56','benchmark':'3119aa4a'}
    excluded={}
    for kind,p in paths.items():
        h=sha(p);assert h.startswith(expected[kind]);pins[str(p)]=h
        data=json.loads(p.read_text());names=set()
        for key in ('rooms','physical_groups','scenes','canonical','natives'):
            values=data.get(key,[])
            names.update(values if isinstance(values,(list,dict)) else [])
        for a,bs in data.get('aliases',{}).items():names.add(a);names.update(bs)
        converted=set()
        for name in names:
            if not isinstance(name,str) or '/' not in name:continue
            ds,sc=name.split('/',1)
            ds={'d1':'scannet','d2':'scannetpp','d3':'arkitscenes','scannetppv2':'scannetpp'}.get(ds,ds)
            native=ds+'/'+sc
            converted.add(native)
            if ds=='scannet':converted.add(re.sub(r'_\d+$','',native))
            elif ds=='arkitscenes' and sc.isdigit():converted.add(rooms.room(native))
        excluded[kind]=converted
    return rooms,excluded


def room_reasons(r,rooms,excluded):
    status,canonical,_=rooms.status(r)
    result=[] if status=='ok' else [status]
    if canonical:
        room=rooms.room(canonical)
        names={room,canonical, r['dataset']+'/'+r['scene']}
        result += [kind for kind,values in excluded.items() if names & values]
    return result


def native_validate(r):
    errors=trace_grammar.validate_row(r)
    if errors:raise ValueError([(e.rule_id,e.line,e.detail) for e in errors])
    packed=direct_row(r)
    assert packed['target']==r['target']
    assert packed['routing']['answer']==r['answer']
    assert r2_grammar.validate_direct(packed['target'],r['student_input']['question'],32)==r['answer']
    row_check(r,'vqa')
    return packed


class WordingFilter:
    def __init__(self):
        self.data=json.loads((ROOT/'inputs/WORDING_CORPUS.json').read_text())
        assert not self.data['parse_failures'],self.data['parse_failures']
        self.by_length=collections.defaultdict(list)
        for s in self.data['questions']:
            b=s.encode('utf-32-le') # Python normalization uses Unicode codepoints; C uses bytes for ASCII below.
            # All actual VSTI questions are ASCII. Non-ASCII held-out wording is handled by the Python path.
            self.by_length[len(s)].append(s)
        lib=ctypes.CDLL(str(ROOT/'inputs/wording_filter.so'))
        self.within=lib.within;self.within.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];self.within.restype=ctypes.c_int
        self.cache={}
    def hit(self,question):
        q=normalize(question)
        if q in self.cache:return self.cache[q]
        n=len(q)
        for m in range(math.ceil(n*(1-THRESHOLD)), math.floor(n/(1-THRESHOLD))+1):
            k=math.floor(THRESHOLD*max(n,m)+1e-12)
            for other in self.by_length[m]:
                if q.isascii() and other.isascii():d=self.within(q.encode(),other.encode(),k)
                else:
                    prev=list(range(m+1))
                    for i,ch in enumerate(q,1):
                        cur=[i]
                        for j,ch2 in enumerate(other,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ch!=ch2)))
                        prev=cur
                    d=prev[m]
                if d<=k:
                    self.cache[q]=dict(normalized_edit_distance=d/max(n,m),heldout_wording_sha256=hashlib.sha256(other.encode()).hexdigest())
                    return self.cache[q]
        self.cache[q]=None
        return None


def option_permutation(r,fact,position):
    choices=[x.split('. ',1)[1] for x in r['student_input']['options']]
    assert fact['semantic'] in choices and len(set(choices))==len(choices)
    choices.remove(fact['semantic'])
    rng=random.Random(str(SEED)+'|'+r['question_type']+'|'+r['qid'])
    rng.shuffle(choices);choices.insert(position,fact['semantic'])
    question=r['student_input']['question']
    if r['question_type'].startswith('camera_'):
        question,n=re.subn(r'\([^()]+\)', '('+', '.join(choices)+')',question,count=1)
        assert n==1
    return choices,question


