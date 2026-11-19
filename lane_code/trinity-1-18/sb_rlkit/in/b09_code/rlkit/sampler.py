"""Sampler: K rollouts per prompt on the tree's native decode path, committed per draw.

    python -m rlkit.sampler --config SAMPLER.json --prompts PROMPTS.jsonl --out RUN_DIR \
        [--shard i/n] [--max-seconds S] [--limit N]

* Decoding is the tree's public `student_pilot.carrier_c1_decode.generate` (prefill with
  carriers, own heads, tool/tower responses, trace sessions, batched token forwards). Only
  the token choice is ours (`forcing.SamplingChoice`, installed by `forcing.sampling_hooks`).
* Seeds derive from (run seed, prompt id, draw index); a draw's text does not depend on
  shard, order, batch size or resume.
* Every draw commits atomically with a checksum and the config hash; resume repeats only
  missing draws and refuses a changed config (`store.DrawStore`).
* Frozen-tower outputs are cached per clip (`towercache.ClipCache`) through the backend factory.
* A failure stops the shard and writes FAILED_<shard>.json; nothing retries automatically.
"""
import argparse
import json
import re
import sys
import time
import traceback
from pathlib import Path

from . import KIT_VERSION
from .common import atomic_write_json, derive_seed, read_jsonl, sha256_file, sha256_obj
from .forcing import SamplingChoice, align, draw_path, encode_exact, forced_text, sampling_hooks
from .store import DrawStore
from .towercache import ClipCache, key_of

PROMPT_SCHEMA = 'rlkit-prompt-v1'
REQUIRED_PROMPT = ('prompt_id', 'type', 'question', 'gt_answer', 'row', 'scene_key', 'source')

SAMPLING_DEFAULTS = dict(draws=8, forced_share=0.5, temperature=0.7, top_p=0.95, seed=17,
                         max_sampled_tokens=4096, batch_draws=True)  # call limit: decode.max_calls
BENCHMARK_TOKENS = ('revsi', 'vsibench', 'vstibench', 'vsti', 'devs1', 'dsibench', 'official999')


def norm_source(value):
    import unicodedata
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKC', str(value)).lower())


def benchmark_source(obj):
    """The first benchmark-looking source/dataset field of a prompt or row (normalised match), else None."""
    fields = []
    for o in (obj, obj.get('row') if isinstance(obj.get('row'), dict) else None):
        if isinstance(o, dict):
            fields += [o.get('source'), o.get('dataset'), o.get('benchmark'), (o.get('provenance') or {}).get('source_kind')
                       if isinstance(o.get('provenance'), dict) else None]
    for f in fields:
        if f is not None and any(t in norm_source(f) for t in BENCHMARK_TOKENS):
            return f
    return None


class PromptError(ValueError):
    pass


def check_prompts(prompts, exclusions):
    """Refuse benchmark items, ReVSI, and any excluded scene before a byte is decoded."""
    seen = set()
    banned_sources = {s.lower() for s in exclusions.get('banned_sources', ())}
    banned_scenes = set(exclusions.get('scene_keys', ()))
    for p in prompts:
        if p.get('schema') != PROMPT_SCHEMA:
            raise PromptError(f'{p.get("prompt_id")}: schema must be {PROMPT_SCHEMA}')
        missing = [k for k in REQUIRED_PROMPT if k not in p]
        if missing:
            raise PromptError(f'{p.get("prompt_id")}: missing {missing}')
        if p['prompt_id'] in seen:
            raise PromptError(f'duplicate prompt id {p["prompt_id"]}')
        seen.add(p['prompt_id'])
        bad = benchmark_source(p)
        if bad is None and any(norm_source(f) in {norm_source(b) for b in banned_sources}
                               for f in (p.get('source'), (p.get('row') or {}).get('source'), (p.get('row') or {}).get('dataset'))
                               if f is not None):
            bad = p.get('source')
        if bad is not None:
            raise PromptError(f'{p["prompt_id"]}: source {bad} is a benchmark; never sampled')
        if p['scene_key'] in banned_scenes:
            raise PromptError(f'{p["prompt_id"]}: scene {p["scene_key"]} is excluded')
    return True


def has_form(forcing, prompt, path):
    return bool((prompt.get('forcing') or {}).get(path) or (forcing.get(prompt['type']) or {}).get(path))


class SamplerConfig:
    def __init__(self, raw):
        self.raw = raw
        unknown = set(raw.get('sampling') or {}) - set(SAMPLING_DEFAULTS)
        if unknown:
            raise ValueError(f'unknown sampling keys {sorted(unknown)} (the call limit is decode.max_calls)')
        s = {**SAMPLING_DEFAULTS, **(raw.get('sampling') or {})}
        self.sampling = s
        self.forcing = raw.get('forcing') or {}
        self.decode = raw.get('decode') or {}  # pose_source, mode ('own'|'shuffle_heads')
        self.identity = dict(kit=KIT_VERSION, export=raw.get('export'), tree=raw.get('tree'),
                             prompts_sha256=raw.get('prompts_sha256'), sampling=s, forcing=self.forcing,
                             decode=self.decode, backend=raw.get('backend'))


def plan_draws(cfg, prompt):
    s = cfg.sampling
    head, direct = has_form(cfg.forcing, prompt, 'head'), has_form(cfg.forcing, prompt, 'direct')
    return [draw_path(d, s['draws'], s['forced_share'], head, direct) for d in range(s['draws'])]


def make_choice(cfg, backend, prompt, draw, path):
    tok = backend.processor.tokenizer
    text = forced_text(cfg.forcing, prompt, path)
    ids = encode_exact(tok, text) if text else []
    s = cfg.sampling
    seed = derive_seed(s['seed'], prompt['prompt_id'], draw)
    return SamplingChoice(ids, seed=seed, temperature=s['temperature'], top_p=s['top_p'],
                          max_sampled_tokens=s['max_sampled_tokens'], eos_id=backend.eos_id()), text


def _slim_calls(calls):
    keep = ('call', 'response', 'at_token', 'forced_tokens', 'kind', 'code', 'spec_version',
            'direct_answer_fallback')
    return [{k: c[k] for k in keep if k in c} for c in calls]


def prompt_ids_sha256(batch):
    """Same digest as grpo_tree student_pilot.grpo_rows.ids_sha256 (json list of ints)."""
    import hashlib
    return hashlib.sha256(json.dumps([int(i) for i in batch['input_ids'][0].tolist()]).encode()).hexdigest()


def response_sources(rec, kw):
    """Where the rollout's printed responses came from: the decode kwargs the sampler passed and
    the decoder's own per-query backend names (heads.ground_queries[].backend)."""
    heads = rec.get('heads') or {}
    queries = heads.get('ground_queries') or []
    gb = kw.get('ground_backend')
    return dict(pose_source=kw.get('pose_source', 'own'), mask_source=kw.get('mask_source'),
                ground_backend=None if gb is None else type(gb).__name__,
                geometry_source=getattr(gb, 'geometry_source', None),
                geometry_identity=getattr(getattr(gb, 'scene', None), 'geometry_identity', None),
                source_identity=getattr(getattr(gb, 'source', None), 'identity', None),
                source_provenance=None if gb is None else str(getattr(getattr(gb, 'source', None), 'provenance', 'unspecified')),
                presence_identity=getattr(getattr(getattr(gb, 'stages', None), 'presence', None), 'identity', None),
                rescue=getattr(getattr(gb, 'stages', None), 'rescue', None) is not None,
                verify_identity=getattr(getattr(gb, 'verify', None), 'identity', None),
                verify_stubbed=None if gb is None else (getattr(gb, 'verify', None) is None
                                                        or bool(getattr(gb.verify, 'stubbed', False))),
                ground_query_backends=sorted({str(q.get('backend')) for q in queries}),
                query_provenance=sorted({str(q.get('source_provenance')) for q in queries}),
                presence_sources=sorted({str(q.get('presence_source')) for q in queries}),
                tower_state=kw.get('tower_state') is not None, verify=kw.get('verify') is not None,
                reread=kw.get('reread') is not None, donor=kw.get('donor_batch') is not None,
                call_kinds=sorted({str(c.get('kind')) for c in rec.get('calls', [])}))


def build_record(prompt, draw, path, text, choice, rec, seconds, prompt_sha=None, sources=None):
    kinds, lt, lr = align(rec, choice)
    own = sum(k in ('f', 's', 'b') for k in kinds)
    return dict(
        schema='rlkit-draw-v1', prompt_id=prompt['prompt_id'], draw=draw, type=prompt['type'],
        path=path, forced_text=text, seed=choice.seed, tokens=rec['tokens'], kinds=''.join(kinds),
        logp_tempered=lt, logp_raw=lr, text=rec['text'], calls=_slim_calls(rec.get('calls', [])),
        finish=rec['finish'], budget_hit=choice.budget_hit, generated_tokens=rec['generated_tokens'],
        own_tokens=own, response_tokens=len(kinds) - own, forced_prefix_tokens=kinds.count('f'),
        prompt_tokens=rec.get('prompt_tokens'), geometry_error=rec.get('geometry_error'),
        errors=rec.get('errors', 0), tower_error=rec.get('tower_error'), seconds=seconds,
        prompt_ids_sha256=prompt_sha, response_sources=sources, temperature=choice.temperature, top_p=choice.top_p)


def sample_prompt(cfg, backend, store, prompt):
    """Decode every missing draw of one prompt; commit each; return per-draw timing rows."""
    paths = plan_draws(cfg, prompt)
    todo = [d for d in range(len(paths)) if store.load(prompt['prompt_id'], d) is None]
    if not todo:
        return []
    t0 = time.time()
    batch = backend.prompt_batch(prompt)
    prompt_sha = prompt_ids_sha256(batch)
    t_batch = time.time() - t0
    made = [(d, paths[d], *make_choice(cfg, backend, prompt, d, paths[d])) for d in todo]
    out = []
    if cfg.sampling['batch_draws'] and backend.can_batch(prompt) and len(made) > 1:
        kw = backend.decode_kwargs(prompt, batch, n=len(made))
        t1 = time.time()
        with sampling_hooks():
            recs = backend.generate([batch] * len(made), [m[2] for m in made], **kw)
        per = (time.time() - t1 + t_batch) / len(made)
        for (d, path, choice, text), rec in zip(made, recs):
            r = build_record(prompt, d, path, text, choice, rec, per, prompt_sha, response_sources(rec, kw))
            store.commit(r)
            out.append(r)
    else:
        for d, path, choice, text in made:
            kw = backend.decode_kwargs(prompt, batch, n=1)
            t1 = time.time()
            with sampling_hooks():
                rec = backend.generate(batch, choice, **kw)
            r = build_record(prompt, d, path, text, choice, rec, time.time() - t1 + t_batch / len(made), prompt_sha,
                             response_sources(rec, kw))
            store.commit(r)
            out.append(r)
    return out


class NativeBackend:
    """Binds the tree's own reader: evalpath.runtime.load_model('routed', ...) and prompt_batch.

    tree_root is put first on sys.path (read only). `factory` ('module:function') optionally
    returns per-prompt decode kwargs (ground_backend, mask_source, pose_source, tower_state)
    and receives the ClipCache so frozen-tower outputs are built once per clip.
    """

    def __init__(self, raw):
        b = raw['backend']
        root = str(Path(b['tree_root']).resolve())
        if root not in sys.path:
            sys.path.insert(0, root)
        from evalpath import runtime
        self.runtime = runtime
        self.cfg = json.loads(Path(b['kit_config']).read_text())
        for over in b.get('config_overrides', []):
            self.cfg.update(json.loads(Path(over).read_text()))
        self.model, self.processor, self.info = runtime.load_model(
            'routed', self.cfg, artifact_pin=b['artifact_pin'], device=b.get('device', 'cuda:0'))
        self.cache = ClipCache(b.get('cache_items', 8), b.get('cache_dir'))
        self.factory = None
        if b.get('factory'):
            mod, fn = b['factory'].split(':')
            self.factory = getattr(__import__(mod, fromlist=[fn]), fn)
        self.decode = raw.get('decode') or {}
        self.export = raw.get('export')
        self.backend_cfg = b

    def eos_id(self):
        return self.processor.tokenizer.eos_token_id

    def prompt_batch(self, prompt):
        batch = self.runtime.prompt_batch(self.processor, prompt['row'], self.cfg, 'routed')
        device = next(self.model.parameters()).device
        return {k: (v.to(device) if hasattr(v, 'to') else v) for k, v in batch.items()}

    def can_batch(self, prompt):
        return self.factory is None  # a ground backend serves one row at a time

    def decode_kwargs(self, prompt, batch, n=1):
        kw = dict(pose_source=self.decode.get('pose_source', 'own'))
        if self.factory is not None:
            kw.update(self.factory(self.model, self.processor, prompt, batch, cache=self.cache, backend_cfg=self.backend_cfg,
                                   key=key_of(video=batch.get('video_sha256'), frames=batch.get('frame_indices'),
                                              export=self.export)))
        return kw

    def generate(self, batch, choice, **kw):
        from student_pilot import carrier_c1_decode as D
        return D.generate(self.model, self.processor, batch, reference_trace=choice,
                          max_calls=self.decode.get('max_calls', 40), **kw)


def shard_of(prompts, shard):
    i, n = shard
    return [p for j, p in enumerate(prompts) if j % n == i]


def run(raw, prompts, out_dir, *, backend=None, shard=(0, 1), max_seconds=None, limit=None):
    cfg = SamplerConfig(raw)
    check_prompts(prompts, raw.get('exclusions') or {})
    store = DrawStore(out_dir, cfg.identity)
    mine = shard_of(prompts, shard)[:limit] if limit else shard_of(prompts, shard)
    progress = Path(out_dir) / 'progress' / ('shard_%d_of_%d.json' % shard)
    start = time.time()
    stats = dict(done_draws=0, seconds=0.0, by_path={})
    try:
        backend = backend or NativeBackend(raw)
        for k, prompt in enumerate(mine):
            if max_seconds is not None and time.time() - start > max_seconds:
                stats['stopped'] = 'max_seconds'
                break
            for r in sample_prompt(cfg, backend, store, prompt):
                stats['done_draws'] += 1
                stats['seconds'] += r['seconds']
                p = stats['by_path'].setdefault(r['path'], dict(n=0, seconds=0.0, own_tokens=0, calls=0))
                p['n'] += 1
                p['seconds'] += r['seconds']
                p['own_tokens'] += r['own_tokens']
                p['calls'] += len(r['calls'])
            atomic_write_json(progress, dict(stats, prompts_done=k + 1, prompts=len(mine),
                                             wall=time.time() - start, at=time.time(),
                                             cache=getattr(getattr(backend, 'cache', None), 'stats', dict)()))
    except Exception:
        atomic_write_json(Path(out_dir) / ('FAILED_shard_%d_of_%d.json' % shard),
                          dict(traceback=traceback.format_exc(), at=time.time(), stats=stats))
        raise
    stats['wall'] = time.time() - start
    atomic_write_json(progress, dict(stats, prompts=len(mine), finished=True, at=time.time()))
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--shard', default='0/1')
    ap.add_argument('--max-seconds', type=float)
    ap.add_argument('--limit', type=int)
    a = ap.parse_args(argv)
    raw = json.loads(Path(a.config).read_text())
    raw['prompts_sha256'] = sha256_file(a.prompts)
    i, n = (int(x) for x in a.shard.split('/'))
    stats = run(raw, read_jsonl(a.prompts), a.out, shard=(i, n), max_seconds=a.max_seconds, limit=a.limit)
    print(json.dumps(stats, sort_keys=True))


if __name__ == '__main__':
    main()
