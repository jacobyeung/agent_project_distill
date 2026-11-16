"""CPU test of direct.py's journal, resume, parity and B2048 logic with a scripted stand-in for vLLM (no model forward).
Cases by item: closed-early thinking (reuse), short unclosed (continue), long unclosed > 2048 tokens (force-close).
Checks: continuation metadata (cap 64, answer tokens), parity runs on resume, resume adds nothing, torn tail repaired,
a row bound to another checkpoint is refused."""
import json, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import direct as D
from transformers import AutoProcessor

tok = AutoProcessor.from_pretrained(str(D.LANE / 'work/model_m544'), local_files_only=True).tokenizer
calls = dict(probe=0, main=0, cont=0)


class Out:
    def __init__(self, text, ids, finish, prompt_ids):
        self.outputs = [types.SimpleNamespace(text=text, token_ids=ids, finish_reason=finish)]
        self.prompt_token_ids = prompt_ids


BAD_TAIL = dict(on=False)


class FakeLLM:
    def __init__(self, **kw):
        self.llm_engine = None

    def generate(self, reqs, params):
        res = []
        for r in reqs:
            pids = r.get('prompt_token_ids') or tok.encode(r['prompt'], add_special_tokens=False)
            if params.max_tokens == 1:
                calls['probe'] += 1; res.append(Out('x', [0], 'length', pids))
            elif params.max_tokens == 64:
                calls['cont'] += 1; ids = tok.encode('B', add_special_tokens=False)
                res.append(Out('B', ids, 'stop', [999] if BAD_TAIL['on'] else pids))
            else:
                calls['main'] += 1
                case = int(D.hashlib.sha256(r['prompt'].encode()).hexdigest(), 16) % 3
                text = ['thought\n</think>\n\nA', 'short thought', 'word ' * 2100][case]
                ids = tok.encode(text, add_special_tokens=False)
                res.append(Out(text, ids, 'stop' if case < 2 else 'length', pids))
        return res


class SP:
    def __init__(self, temperature=0, max_tokens=1):
        self.temperature, self.max_tokens = temperature, max_tokens


sys.modules['vllm'] = types.SimpleNamespace(LLM=FakeLLM, SamplingParams=SP, __version__='fake')
import parity
parity.compare = lambda processor, engine, t, arrays, meta, ids, pixels=False, cell=None: dict(
    example_id=t['example_id'], prompt_equal=True, **({'pixels': {'pass': True}} if pixels else {}))
W = D.LANE / f'work/synth/direct_{int(time.time())}'
args = types.SimpleNamespace(model=str(D.LANE / 'work/model_m544'), split='heldout', types='obj_appearance_order,object_counting',
                             limit=9, chunk=4, max_seqs=4, max_model_len=24576, out=str(W))
checks = {}
D.gpu_read(args)
rows = [json.loads(l) for l in open(W / 'journal.jsonl')]
checks['nine_rows'] = len(rows) == 9 and len({r['example_id'] for r in rows}) == 9
cont = [r for r in rows if r['B2048_meta']['forced_close'] or r['B2048_meta']['stopped_unclosed']]
reuse = [r for r in rows if r not in cont]
checks['has_all_cases'] = bool(reuse) and any(r['B2048_meta']['stopped_unclosed'] for r in rows) and any(r['B2048_meta']['forced_close'] for r in rows)
checks['cont_meta'] = all(r['B2048']['max_new_tokens'] == 64 and r['B2048']['output_tokens'] == r['B2048_meta']['answer_tokens'] > 0
                          and r['B2048_answer_text'] == 'B' for r in cont)
checks['cont_scored_B'] = all(r['B2048']['extracted_answer'] == 'B' for r in cont)
checks['reuse_is_full'] = all(r['B2048'] == r['full'] for r in reuse)
checks['bound'] = all(isinstance(r.get('binding'), str) and len(r['binding']) == 64 for r in rows)
p0, m0 = calls['probe'], calls['main']
with open(W / 'journal.jsonl', 'a') as f:
    f.write('{"status": "comp')
D.gpu_read(args)
checks['resume_parity_rerun'] = calls['probe'] == p0 + 9
checks['resume_no_new_generation'] = calls['main'] == m0
checks['torn_repaired'] = len(list(W.glob('journal.torn.*'))) == 1 and \
    all(json.loads(l) for l in open(W / 'journal.jsonl')) and sum(1 for _ in open(W / 'journal.jsonl')) == 9
raw = (W / 'journal.jsonl').read_bytes()
(W / 'journal.jsonl').write_bytes(raw.rstrip(b'\n'))
args9 = types.SimpleNamespace(**{**vars(args), 'limit': 10})
D.gpu_read(args9)
lines10 = open(W / 'journal.jsonl').read().splitlines()
checks['unterminated_kept'] = len(lines10) == 10 and all(json.loads(l) for l in lines10) and \
    len(list(W.glob('journal.torn.*'))) == 1
args12 = types.SimpleNamespace(**{**vars(args), 'limit': 16, 'out': str(W) + '_tail'})
BAD_TAIL['on'] = True
try:
    D.gpu_read(args12); checks['bad_tail_refused'] = False
except SystemExit as e:
    checks['bad_tail_refused'] = 'prefix + close' in str(e)
BAD_TAIL['on'] = False
lines = open(W / 'journal.jsonl').read().splitlines()
r0 = json.loads(lines[0]); r0['binding'] = '0' * 64
(W / 'journal.jsonl').write_text('\n'.join([json.dumps(r0)] + lines[1:]) + '\n')
try:
    D.gpu_read(args); checks['stale_refused'] = False
except SystemExit as e:
    checks['stale_refused'] = 'another binding' in str(e)
print(json.dumps(dict(checks=checks, calls=calls)))
(D.LANE / 'out/tests/DIRECT_FAKE_ENGINE.json').write_text(json.dumps(dict(checks=checks, calls=calls, run=str(W)), indent=1) + '\n')
print('PASS' if all(checks.values()) else 'FAIL')
