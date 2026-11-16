"""Shared paths, loaders and conventions for the DOSE-1 traced pool (lane dose_pool, 2026-11-11).

Inputs are read-only files on trinity-2-18 /scratch; outputs go to /scratch/jjyeung/orch_cd/dose_pool/out."""
import hashlib
import json
import re

L = '/scratch/jjyeung/orch_cd/dose_pool'
W = f'{L}/work/dosepool'
OUT = f'{L}/out'
V = '/scratch/jjyeung/orch_cd/weak_data/in/v590kgt'
QUESTIONS = f'{V}/inv/QUESTIONS.jsonl'
BENCH = '/scratch/jjyeung/orch_cd/weak_data/inputs/VSIBENCH_meta_5130.jsonl'
REAL = ('scannet', 'scannetppv2', 'arkitscenes')
DCODE = {'scannet': 'd1', 'scannetppv2': 'd2', 'arkitscenes': 'd3'}
FPS = {'scannet': 30.0, 'scannetppv2': 60.0, 'arkitscenes': 10.0}

# VSI-590K type -> VSI-Bench type whose answer shares the pool matches (None: no benchmark counterpart)
BENCH_TYPE = {'absolute_count': 'object_counting', 'absolute_distance_object': 'object_abs_distance',
              'absolute_size_object': 'object_size_estimation', 'absolute_size_room': 'room_size_estimation',
              'relative_distance_object': 'object_rel_distance', 'appearance_order': 'obj_appearance_order',
              'relative_direction_object': None, 'absolute_direction_object': None, 'relative_count': None,
              'relative_size_object': None}
MC = {'relative_direction_object', 'relative_distance_object', 'relative_count', 'relative_size_object', 'appearance_order'}


def sha256_file(p, n=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(n)
            if not b:
                return h.hexdigest()
            h.update(b)


def hseed(*parts):
    return int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:16], 16)


def load_questions():
    return [q for q in map(json.loads, open(QUESTIONS)) if q['dataset'] in REAL]


def split_question(text):
    """VSI-590K prompt -> (core question, options list). Drops the frames preamble, the option block and post-prompt."""
    t = re.sub(r'^\s*These are frames of a video\.\s*', '', text)
    opts = []
    m = re.search(r'\nOptions:\n(.*?)(?:\nAnswer with|\Z)', t, re.S)
    if m:
        opts = [o.strip() for o in m.group(1).strip().split('\n') if re.match(r'^[A-Z]\.\s', o.strip())]
        t = t[:m.start()]
    t = re.sub(r'\n?Please answer the question using a single word or phrase\.?\s*$', '', t.strip())
    return t.strip(), opts


def option_texts(opts):
    return {o[0]: o[3:].strip() for o in opts}


def rel_direction_bench(opts):
    n = len(opts)
    return {2: 'object_rel_direction_easy', 3: 'object_rel_direction_medium', 4: 'object_rel_direction_hard'}.get(n)


UNIT = [('square feet', 'sqft'), ('square foot', 'sqft'), ('sq ft', 'sqft'), ('square meter', 'sqm'), ('square metre', 'sqm'),
        ('millimeter', 'mm'), ('millimetre', 'mm'), ('centimeter', 'cm'), ('centimetre', 'cm'), ('inch', 'in'),
        ('feet', 'ft'), ('foot', 'ft'), ('meter', 'm'), ('metre', 'm')]
TO_CM = {'mm': 0.1, 'cm': 1.0, 'm': 100.0, 'in': 2.54, 'ft': 30.48}
TO_SQM = {'sqm': 1.0, 'sqft': 0.09290304}
UNAME = {'mm': 'millimeters', 'cm': 'centimeters', 'm': 'meters', 'in': 'inches', 'ft': 'feet', 'sqm': 'square meters',
         'sqft': 'square feet'}


def question_unit(text):
    t = text.lower()
    for k, u in UNIT:
        if k in t:
            return u
    return None


def num(s):
    try:
        return float(str(s).strip())
    except ValueError:
        return None


def fmt(x, d=2):
    s = ('%.' + str(d) + 'f') % x
    return s.rstrip('0').rstrip('.') if '.' in s else s
