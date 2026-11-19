"""Head-use tracking at every eval checkpoint of an RL run (USER 2026-11-16 ~05:00 PT).

    python -m rlkit.headuse report --run RUN_DIR --prompts SET.jsonl --label r1 [--expected EXPECTED.json] \
        [--usage USAGE.json] [--reward-config R.json] --out HEADUSE_r1.json
    python -m rlkit.headuse usage  --config SAMPLER.json --run RUN_DIR --prompts SET.jsonl --out USAGE.json [--limit N]
    python -m rlkit.headuse curve  --reports HEADUSE_r0.json HEADUSE_r1.json ... --out CURVE.md

Per type, from the checkpoint's rollouts on a fixed item set (the same set at every checkpoint,
so SFT and RL curves pair; h1_headsft's evaluator sets replace the default set when they exist):
  call_rate        share of rollouts with at least one head call; free_call_rate over unforced draws
  heads            count of each called head (call opener: ground, gap, depth_at, move, turn, pose, ...)
  placement        against the type's expected head sequence (EXPECTED.json, default from the
                   trained program traces): exact, superset (expected is a subsequence), missing,
                   or none (no call); estimate_first flags a stated measurement before the first call
  usage            counterfactual: the draw's forced span decoded greedily twice, with the printed
                   responses and with every unit-bearing value in them scaled by 1.37; usage_rate =
                   share of called rollouts whose answer moves (numbers: relative change > 5%;
                   options: letter); unparsed answers are counted apart, never as moved
  reward split     mean c, g, r, n and length term for rollouts that called a head and that did not;
                   the length term charges call tokens, so this split shows whether it pushes the
                   policy off its heads
`curve` lines up the reports by checkpoint: mean reward next to each type's call rate, placement and
usage, so a reward rise with falling head use where heads beat direct answers is visible.
"""
import argparse
import json
import re
from contextlib import contextmanager
from pathlib import Path

from .common import atomic_write_bytes, atomic_write_json, read_jsonl
from .gate import FAILED_RESPONSE, NUM, RESPONSE
from .reward import DEFAULTS as REWARD_DEFAULTS, score_group
from .store import DrawStore

SCALE = 1.37
OPENER = re.compile(r'<([a-z][a-z_0-9]*)')
EXPECTED_DEFAULT = {'object_abs_distance': ['ground', 'ground', 'gap']}
STATED = re.compile(r'\d+(?:\.\d+)?\s*(?:m|cm|mm|ft|feet|in|inches|m\^2|m²|square met(?:er|re)s?)(?![A-Za-z])')


NOT_HEAD_KINDS = ('calculator', 'error')


def head_call(c):
    """A call counts as head use when a head served it: not a calculator or error response, and the
    printed response did not fail ('not seen', 'error: ...')."""
    return c.get('kind') not in NOT_HEAD_KINDS and not FAILED_RESPONSE.search(str(c.get('response', '')))


def openers(rec):
    out = []
    for c in rec.get('calls', []):
        if head_call(c):
            m = OPENER.match(c.get('call') or '')
            out.append(m.group(1) if m else 'unknown')
    return out


def is_subsequence(small, big):
    it = iter(big)
    return all(x in it for x in small)


def placement(rec, expected):
    seq = openers(rec)
    if not seq:
        return 'none'
    if expected is None:
        return 'unspecified'
    if seq == expected:
        return 'exact'
    return 'superset' if is_subsequence(expected, seq) else 'missing'


def estimate_first(rec):
    """A stated measurement in the model's own text before the first head call."""
    calls = [c for c in rec.get('calls', []) if head_call(c)]
    if not calls:
        return False
    first = rec['text'].find(calls[0].get('call') or '\0')
    return first > 0 and STATED.search(RESPONSE.sub('', rec['text'][:first])) is not None


def moved(a, b, options):
    if a is None or b is None:
        return a != b
    if options:
        return str(a).strip().upper() != str(b).strip().upper()
    try:
        x, y = float(a), float(b)
    except ValueError:
        return a != b
    return abs(x - y) > 0.05 * max(abs(x), 1e-9)


def summarize(prompts, groups, reward_cfg=None, expected=None, usage=None):
    expected = {**EXPECTED_DEFAULT, **(expected or {})}
    usage = usage or {}
    cfg = {**REWARD_DEFAULTS, **(reward_cfg or {})}
    types, rewards = {}, []
    for p in prompts:
        recs = groups.get(p['prompt_id']) or []
        if not recs:
            continue
        for rec, sc in zip(recs, score_group(p, recs, cfg)):
            t = types.setdefault(p['type'], dict(n=0, called=0, free=0, free_called=0, heads={}, placement={},
                                                 estimate_first=0, split={'called': [], 'not_called': []},
                                                 usage_n=0, usage_moved=0, usage_unparsed=0))
            calls = openers(rec)
            t['n'] += 1
            t['called'] += bool(calls)
            if rec['path'] == 'free':
                t['free'] += 1
                t['free_called'] += bool(calls)
            for h in calls:
                t['heads'][h] = t['heads'].get(h, 0) + 1
            pl = placement(rec, expected.get(p['type']))
            t['placement'][pl] = t['placement'].get(pl, 0) + 1
            t['estimate_first'] += estimate_first(rec)
            t['split']['called' if calls else 'not_called'].append(
                dict(c=sc['c'], g=sc['g'], r=sc['r'], n=sc['n'], length_term=sc['length_term']))
            rewards.append(sc['r'])
            u = usage.get(f'{p["prompt_id"]}|{rec["draw"]}')
            if u is not None and calls:
                if u['moved'] is None:
                    t['usage_unparsed'] += 1
                else:
                    t['usage_n'] += 1
                    t['usage_moved'] += bool(u['moved'])
    out = {}
    for qtype, t in sorted(types.items()):
        split = {k: (dict(rollouts=len(v), **{m: sum(x[m] for x in v) / len(v) for m in ('c', 'g', 'r', 'n', 'length_term')})
                     if v else dict(rollouts=0)) for k, v in t['split'].items()}
        out[qtype] = dict(rollouts=t['n'], call_rate=t['called'] / t['n'],
                          free_call_rate=t['free_called'] / t['free'] if t['free'] else None, heads=t['heads'],
                          placement=t['placement'], expected=expected.get(qtype),
                          estimate_first_rate=t['estimate_first'] / max(1, t['called']),
                          usage_rate=t['usage_moved'] / t['usage_n'] if t['usage_n'] else None, usage_n=t['usage_n'],
                          usage_unparsed=t['usage_unparsed'],
                          reward_split=split)
    return dict(types=out, mean_reward=sum(rewards) / len(rewards) if rewards else None, rollouts=len(rewards))


UNIT = r'(?:m\^2|m²|m2|sq\s*m|square met(?:er|re)s?|m|cm|mm|ft|feet|in|inches|deg|degrees|°)(?![A-Za-z])'
TUPLE = re.compile(r'\(([^()]*)\)(\s*' + UNIT + ')')
CHAIN = re.compile(r'(' + NUM + r'(?:\s*[x×]\s*' + NUM + r')*)(\s*' + UNIT + ')')
NUMBER = re.compile(NUM)


def _scale_numbers(text, scale):
    def one(m):
        digits = len(m.group(0).split('.')[1]) if '.' in m.group(0) else 0
        return f'{float(m.group(0)) * scale:.{max(digits, 2)}f}'
    return NUMBER.sub(one, text)


def perturb_text(text, scale=SCALE):
    """Scale every value that carries a unit: coordinate tuples `(x, y, z) m`, chains `a x b x c m`,
    and single values `3.22 m` / `45 deg`. Frame numbers, labels and counts stay."""
    text = TUPLE.sub(lambda m: '(' + _scale_numbers(m.group(1), scale) + ')' + m.group(2), text)
    return CHAIN.sub(lambda m: _scale_numbers(m.group(1), scale) + m.group(2), text)


@contextmanager
def perturbed_responses(scale=SCALE):
    """Scale every unit-bearing value in the decoder's printed responses (process-local, reversible).
    The decoder (carrier_c1_batch_decode.Row._call) reads D.respond_state at call time."""
    from student_pilot import carrier_c1_decode as D
    original = D.respond_state

    def respond(state, call_text, registry):
        text, info = original(state, call_text, registry)
        return perturb_text(text, scale), info
    D.respond_state = respond
    try:
        yield
    finally:
        D.respond_state = original


def usage_for(raw, backend, prompts, groups, limit=None, scale=SCALE):
    """Counterfactual usage of called draws: the same forced span, decoded greedily twice, once with the
    printed responses and once with them perturbed, so sampling noise cannot move the answer.
    {prompt_id|draw: {moved, answer, perturbed_answer, responses}}; moved is None when either answer
    fails to parse (reported separately, never counted as moved)."""
    from . import sampler as S
    from .forcing import SamplingChoice, encode_exact, forced_text
    from .score import score
    cfg = S.SamplerConfig(raw)
    out, done = {}, 0
    tok = backend.processor.tokenizer
    for p in prompts:
        for rec in groups.get(p['prompt_id']) or []:
            if not openers(rec) or (limit is not None and done >= limit):
                continue
            text = forced_text(cfg.forcing, p, rec['path'])
            prefix = encode_exact(tok, text) if text else []

            def decode(perturb):
                choice = SamplingChoice(prefix, seed=rec['seed'], temperature=1.0, top_p=1e-9,
                                        max_sampled_tokens=cfg.sampling['max_sampled_tokens'], eos_id=backend.eos_id())
                batch = backend.prompt_batch(p)
                kw = backend.decode_kwargs(p, batch, n=1)
                with S.sampling_hooks():
                    if perturb:
                        with perturbed_responses(scale):
                            return backend.generate(batch, choice, **kw)
                    return backend.generate(batch, choice, **kw)
            base, new = decode(False), decode(True)
            a, b = score(p, base['text'])['answer'], score(p, new['text'])['answer']
            out[f'{p["prompt_id"]}|{rec["draw"]}'] = dict(
                moved=None if a is None or b is None else moved(a, b, p.get('options')), answer=a, perturbed_answer=b,
                responses=[c['response'] for c in new.get('calls', [])], base_responses=[c['response'] for c in base.get('calls', [])])
            done += 1
    return out


def curve(reports):
    lines = ['| checkpoint | mean r | type | call rate | free call rate | exact placement | usage rate | r called | r not called | length term called |',
             '|---|---|---|---|---|---|---|---|---|---|']
    f = lambda v: '-' if v is None else f'{v:.3f}'  # noqa: E731
    for rep in reports:
        for qtype, t in rep['types'].items():
            pl = t['placement']
            exact = pl.get('exact', 0) / max(1, sum(v for k, v in pl.items() if k != 'none'))
            sc, sn = t['reward_split']['called'], t['reward_split']['not_called']
            lines.append(f'| {rep["label"]} | {f(rep["mean_reward"])} | {qtype} | {f(t["call_rate"])} | {f(t["free_call_rate"])} | '
                         f'{f(exact)} | {f(t["usage_rate"])} | {f(sc.get("r"))} | {f(sn.get("r"))} | {f(sc.get("length_term"))} |')
    return '\n'.join(lines) + '\n'


def load_groups(run, prompts):
    head = json.loads((Path(run) / 'RUN_CONFIG.json').read_text())
    store = DrawStore(run, head['config'])
    return store.groups(prompts, head['config']['sampling']['draws'], require_complete=False), head


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('report')
    for a in ('--run', '--prompts', '--label', '--out'):
        r.add_argument(a, required=True)
    for a in ('--expected', '--usage', '--reward-config'):
        r.add_argument(a)
    u = sub.add_parser('usage')
    for a in ('--config', '--run', '--prompts', '--out'):
        u.add_argument(a, required=True)
    u.add_argument('--limit', type=int)
    c = sub.add_parser('curve')
    c.add_argument('--reports', nargs='+', required=True)
    c.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    if a.cmd == 'curve':
        text = curve([json.loads(Path(x).read_text()) for x in a.reports])
        atomic_write_bytes(a.out, text.encode())
        print(text)
        return
    prompts = read_jsonl(a.prompts)
    groups, head = load_groups(a.run, prompts)
    if a.cmd == 'usage':
        from .sampler import NativeBackend
        raw = json.loads(Path(a.config).read_text())
        result = usage_for(raw, NativeBackend(raw), prompts, groups, a.limit)
    else:
        load = lambda x: json.loads(Path(x).read_text()) if x else None  # noqa: E731
        result = dict(summarize(prompts, groups, load(a.reward_config), load(a.expected), load(a.usage)),
                      label=a.label, run_config_hash=head['config_hash'])
    atomic_write_json(a.out, result)
    print(json.dumps(result, sort_keys=True)[:3000])


if __name__ == '__main__':
    main()
