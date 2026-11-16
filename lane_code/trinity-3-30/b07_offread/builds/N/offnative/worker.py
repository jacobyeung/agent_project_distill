"""Ordered phases, journals, deadline admission, and full-cohort arm construction."""
from copy import deepcopy
import time
from .paths import V1, module
from .io import dump, journal, digest, owned
from .proof import compare
from .cohort import canary
from offkit.report import ReadMode, check_cohort, key, index
PHASES = ('stage','frames','towers','proof','canary','read','score')

class PhaseFailure(RuntimeError):
    pass

def merge(expected, shards):
    if len(set(expected)) != len(expected):
        raise ValueError('duplicate expected item')
    result = index([r for shard in shards for r in shard], 'worker union')
    if set(result) != set(expected):
        raise ValueError('worker union differs from full id list')
    return [result[k] for k in expected]

def arms(primary, unserved, items, kind):
    if kind != 'harness':
        return {'primary':primary}
    p, u = index(primary, 'primary'), index(unserved, 'unserved')
    routed = {key(r) for r in items if r['question_type'].startswith(('object_abs_distance','room_size_estimation'))}
    if set(u) != routed:
        raise ValueError('unserved decode must cover all distance and room items')
    fallback, room = [], []
    for item in items:
        k = key(item)
        f = u[k] if k in routed and p[k]['refusal'] else p[k]
        q = u[k] if item['question_type'].startswith('room_size_estimation') else p[k]
        fallback.append(dict(f, arm='secondary_fallback'))
        room.append(dict(q, arm='secondary_room_unserved'))
    return dict(primary=primary, secondary_fallback=fallback, secondary_room_unserved=room)

class Worker:
    def __init__(self, config, binding, items, runtime, scorer, out, *, fixture=False):
        self.config, self.binding, self.items = config, binding, items
        self.runtime, self.scorer, self.out = runtime, scorer, owned(out)
        self.fixture = fixture
        if bool(getattr(runtime, 'synthetic', False)) != fixture:
            raise ValueError('runtime synthetic status differs from the worker mode')
        if (binding['mode'] == 'fixture') != fixture:
            raise ValueError('fixture binding cannot become a production read')
        if config.get('binding_sha256', config.get('x0')) != binding['binding_sha256']:
            raise ValueError('worker config names another binding')
        self.mode = ReadMode(binding['benchmark'], binding['reader']['kind'])
        if fixture:
            self.mode.items = len(items)
            self.mode.spec = dict(self.mode.spec, scenes=len({(r['dataset'],r['scene_name']) for r in items}))
        check_cohort(self.mode, items)
        index(items, 'cohort')
        self.budget = module('_native_v1_budget', V1/'budget.py').Budget(config.get('deadline_utc'))
        self.decoded = {}; self.unserved = {}; self.official_decodes = 0
        self.proof_pass = False

    def phase(self, name, operation):
        start = time.monotonic()
        receipt = dict(phase=name, binding_sha256=self.binding['binding_sha256'],
                       config_sha256=digest(self.config), fixture=self.fixture)
        try:
            value = operation()
            receipt.update(status='PASS', result=value)
        except Exception as exc:
            receipt.update(status='FAIL', error=type(exc).__name__, detail=str(exc),
                           official_decodes=self.official_decodes)
            raise PhaseFailure(name) from exc
        finally:
            receipt['seconds'] = time.monotonic()-start
            dump(self.out/'receipts'/f'{PHASES.index(name):02d}.json', receipt)

    def generate(self, item, served=True):
        if not self.proof_pass:
            raise ValueError('official decode attempted before identity proof')
        if not self.budget.allows(item['question_type']):
            raise TimeoutError('item-start cutoff reached; preserve return reserve')
        start = time.monotonic()
        decoded = self.runtime.reader.generate(self.runtime.frames_for(item), item, served=served)
        self.budget.observe(item['question_type'], time.monotonic()-start)
        self.official_decodes += 1
        journal(self.out/'decode.jsonl', dict(id=key(item), served=served, decode=decoded))
        return decoded

    def proof(self):
        reference, actual = self.runtime.proof()
        from .proof import CAMERA
        if (len(reference) != 10 or sum(r['question_type'] in CAMERA for r in reference) != 5
                or sum(r['question_type'] == 'object_abs_distance' for r in reference) != 5):
            raise ValueError('proof needs five camera and five distance items')
        result = compare(reference, actual, self.binding['reader']['kind'])
        dump(self.out/'PROOF.json', result)
        if not result['passed']:
            raise ValueError('identity proof mismatch')
        self.proof_pass = True
        return result

    def canary(self):
        ids = canary(self.items, self.mode)
        by_id = index(self.items, 'cohort')
        for k in ids:
            item = by_id[k]
            decoded = self.generate(item)
            if not self.runtime.reader.replay(decoded):
                raise ValueError('canary response replay differs')
            score = self.scorer.score(item, decoded, 'primary')
            if score != self.scorer.score(item, deepcopy(decoded), 'primary'):
                raise ValueError('strict score recomputation differs')
            self.decoded[k] = decoded
        return dict(ids=ids, strict_scores_equal=True, byte_equal_replay=True)

    def read(self):
        for item in self.items:
            k = key(item)
            if k not in self.decoded:
                self.decoded[k] = self.generate(item)
            if self.binding['reader']['kind']=='harness' and item['question_type'].startswith(('object_abs_distance','room_size_estimation')):
                self.unserved[k] = self.generate(item, served=False)
        merge([key(i) for i in self.items], [[dict(id=k) for k in self.decoded]])
        return dict(primary=len(self.decoded), unserved=len(self.unserved), budget=self.budget.record())

    def score(self):
        primary = [self.scorer.score(i, self.decoded[key(i)], 'primary') for i in self.items]
        unserved = [self.scorer.score(i, self.unserved[key(i)], 'unserved') for i in self.items if key(i) in self.unserved]
        result = arms(primary, unserved, self.items, self.binding['reader']['kind'])
        ids = [key(i) for i in self.items]
        for arm, records in result.items():
            complete = merge(ids, [records])
            for r in complete:
                journal(self.out/(arm+'.jsonl'), r)
        dump(self.out/'COMPLETE.json', dict(complete=True, fixture=self.fixture, items=len(ids),
             ids_sha256=digest(ids), binding_sha256=self.binding['binding_sha256'], arms=list(result)))
        return dict(arms=list(result), items=len(ids))

    def run(self):
        if self.out.exists():
            raise ValueError('worker output exists; reruns require a new destination')
        self.out.mkdir(parents=True)
        for name, op in [('stage',lambda:self.runtime.stage(self.config)),
                         ('frames',lambda:self.runtime.frames(self.binding['read_config']['frames'])),
                         ('towers',lambda:self.runtime.towers(self.binding['reader'])),
                         ('proof',self.proof),('canary',self.canary),('read',self.read),('score',self.score)]:
            self.phase(name, op)
        return self.out/'COMPLETE.json'
