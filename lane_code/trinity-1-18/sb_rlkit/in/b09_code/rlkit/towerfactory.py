"""Head-path decode kwargs for the sampler: the reader's own grounding backend.

`s1_grounding` builds what `evalpath/run.py` builds for a routed read of a 3.14 program model:
`student_pilot.s1_grounding.build_backend(row, batch, artifact_pin, audit_dir, settings)` and
mask_source 'mdg'. Config (sampler config backend.factory_config):
  audit_root  directory for per-draw grounding audits (on /scratch)
  settings    the reader's `grounding` settings (ground_candidate_policy, geometry_manifest,
              depth_source, allow_own_fallback)
  reuse       'draw' (default): a fresh backend for every draw, so no session state crosses draws;
              'clip': one backend per clip through the ClipCache. Use 'clip' only after the dry run
              shows byte-equal records for both settings on the same draws (DRYRUN step 3).
Models whose trace_program_version is not 3.14 get no grounding kwargs, as in the reader.
"""
from pathlib import Path

from .common import sha256_obj

_COUNTER = {}


def s1_grounding(model, processor, prompt, batch, *, cache, key, backend_cfg):
    if getattr(model, 'trace_program_version', None) != '3.14':
        return {}
    from student_pilot.s1_grounding import build_backend
    fc = backend_cfg.get('factory_config') or {}
    reuse = fc.get('reuse', 'draw')
    if reuse not in ('draw', 'clip'):
        raise ValueError('factory_config.reuse must be draw or clip')
    row = {**prompt['row'], 'question_type': prompt['type']}
    root = Path(fc['audit_root']) / sha256_obj(prompt['prompt_id'])[:24]

    def build(tag):
        return build_backend(row, batch, backend_cfg['artifact_pin'], root / tag, fc.get('settings'))

    if reuse == 'clip':
        backend = cache.get(key, lambda: build('clip'))
    else:
        n = _COUNTER[prompt['prompt_id']] = _COUNTER.get(prompt['prompt_id'], -1) + 1
        backend = build('d%03d' % n)
    return dict(ground_backend=backend, mask_source='mdg')
