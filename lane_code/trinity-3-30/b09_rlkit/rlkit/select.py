"""Mode (a) selector and row writer: keep the best right rollout per prompt.

    python -m rlkit.select --run RUN_DIR --prompts POOL.jsonl --tree TREE --round R \
        [--reward-config R.json] [--floor FLOOR.json] [--min-c 1.0] --out SELECT_DIR

Per prompt, candidates are rollouts with g = 1 and c >= min_c (default 1.0: exact option, or
MRA 1.0, i.e. within 5% relative error). The winner has the highest reward r, then the fewest
own tokens, then the lowest draw index. The winner's file depends on its path and type:
  vqa_rows.jsonl          direct winners, written in the native VQA row schema (the prompt's own
                          row with target = the rollout's think body and answer) and admitted by
                          the tree's `r2_contract.validate(row, 'vqa')`; refusals go to refused.jsonl
  own_rows.jsonl          head winners whose printed responses all came from heads inside the
                          artifact (`artifact_policy`), as exact-token rows (rlkit-own-row-v1):
                          the trainer's routing stream trains them by cross-entropy on the model's
                          own tokens with the responses masked (grpo_tree student_pilot/grpo_rows.py)
  barred.jsonl            head winners with a response from outside the artifact (another model's
                          heads, a harness responder, an unlisted backend), with the reason
  quarantine.jsonl        only with quarantine_direct_majority=True: head winners on direct-majority
                          types, held for brief 08's amendment (default off: they train like any other)
  no_winner.jsonl         prompts with no right, valid rollout
A head winner never falls back to a direct rollout (that would bias the kept paths toward
direct); `fallback_direct=True` changes this and is recorded in the report.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

from . import KIT_VERSION
from .common import atomic_write_json, read_jsonl, sha256_obj, write_jsonl_atomic
from .gate import SPECIAL_TAIL
from .reward import DEFAULTS as REWARD_DEFAULTS, score_group
from .store import DrawStore

SELECT_DEFAULTS = dict(min_c=1.0, fallback_direct=False, quarantine_direct_majority=False)
OWN_SCHEMA = 'rlkit-own-row-v1'
# Response sources inside the artifact: the model's own pose head or the frozen tower scale shipped
# with it, the own MDG mask head behind the GroundV3 grounding layer, and the decoder's printed
# calculator and error responses. Anything else (a donor model's heads, a harness responder, a
# verify or reread session, an unknown backend) is outside and bars the rollout.
ARTIFACT_POLICY = dict(pose_sources=('own', 'tower'), mask_sources=(None, 'mdg'), ground_backends=('ground_v3', 'mdg'),
                       ground_backend_types=(None, 'GroundV3'), call_kinds=('head', 'calculator', 'error', 'ground', 'gap'),
                       geometry_sources=(None, 'same_checkpoint_own'), geometry_prefixes=('same_checkpoint_own:',),
                       source_prefixes=('native_mdg:',), query_provenance=('unspecified', 'None'), presence_sources=('None',),
                       source_provenances=('unspecified',), presence_identities=(None,), verify_identities=())


def artifact_policy(rec, policy=None):
    """None when every printed response came from inside the artifact, else the first reason."""
    p = {**ARTIFACT_POLICY, **(policy or {})}
    src = rec.get('response_sources')
    if src is None:
        return 'record has no response_sources'
    if src.get('donor'):
        return 'responses from a donor model'
    if src['pose_source'] not in p['pose_sources']:
        return f'pose source {src["pose_source"]} is outside the artifact'
    if src['mask_source'] not in p['mask_sources']:
        return f'mask source {src["mask_source"]} is outside the artifact'
    if src['ground_backend'] not in p['ground_backend_types']:
        return f'ground backend {src["ground_backend"]} is outside the artifact'
    if src.get('verify') or src.get('reread') or src.get('tower_state'):
        return 'a verify, reread or tower-state session served responses'
    allowed = p['ground_backends'] + (('None',) if src['ground_backend'] is None else ())  # own grounding head
    bad = [b for b in src['ground_query_backends'] if b not in allowed]
    if bad:
        return f'ground query backends {bad} are outside the artifact'
    if src['ground_backend'] is not None:
        if src.get('geometry_source') not in p['geometry_sources']:
            return f'geometry source {src.get("geometry_source")} is outside the artifact'
        gid, sid = str(src.get('geometry_identity')), str(src.get('source_identity'))
        if not gid.startswith(p['geometry_prefixes']) or not sid.startswith(p['source_prefixes']):
            return f'grounding identities {gid} / {sid} are outside the artifact'
        if gid.split(':', 1)[1] != sid.split(':', 1)[1]:
            return 'grounding geometry and mask source name different artifacts'
        if src.get('source_provenance', 'missing') not in p['source_provenances']:
            return f'mask source provenance {src.get("source_provenance")} is outside the artifact'
        if src.get('presence_identity', 'missing') not in p['presence_identities']:
            return f'presence prior {src.get("presence_identity")} is outside the artifact'
        if src.get('rescue', True):
            return 'a rescue stage served candidates'
        if not (src.get('verify_stubbed') or src.get('verify_identity') in p['verify_identities']):
            return f'verifier {src.get("verify_identity")} is not stubbed or listed'
    bad = [q for q in src.get('query_provenance', ['missing']) if q not in p['query_provenance']]
    if bad:
        return f'query provenance {bad} is outside the artifact'
    bad = [q for q in src.get('presence_sources', ['missing']) if q not in p['presence_sources']]
    if bad:
        return f'presence sources {bad} are outside the artifact'
    bad = [k for k in src['call_kinds'] if k not in p['call_kinds']]
    if bad:
        return f'call kinds {bad} are outside the policy'
    return None


def winner(scored, min_c, path=None):
    pool = [s for s in scored if s['g'] == 1 and s['c'] >= min_c and (path is None or s['path'] == path)]
    if not pool:
        return None
    return sorted(pool, key=lambda s: (-s['r'], s['n'], s['draw']))[0]


def think_target(text):
    """Native target of a direct rollout: the prompt's `<think>\\n` plus the generated suffix."""
    return '<think>\n' + SPECIAL_TAIL.sub('', text)


def vqa_row(prompt, rec, sc, round_tag):
    row = copy.deepcopy(prompt['row'])
    row.update(target=think_target(rec['text']), answer=str(sc['answer']),
               question_type=prompt['type'], qid=f'{row.get("qid", prompt["prompt_id"])}-{round_tag}d{rec["draw"]}')
    row['rl_selection'] = dict(kit=KIT_VERSION, round=round_tag, prompt_id=prompt['prompt_id'], draw=rec['draw'],
                               seed=rec['seed'], forced=rec['path'], r=sc['r'], c=sc['c'], n=sc['n'],
                               gt_answer=str(prompt['gt_answer']), record_sha256=sha256_obj(rec))
    return row


def own_row(prompt, rec, sc, round_tag):
    if rec.get('prompt_ids_sha256') is None:
        raise ValueError('record lacks prompt_ids_sha256')
    return dict(schema=OWN_SCHEMA, prompt_row=prompt['row'], stream='routing' if 'r' in rec['kinds'] else 'vqa',
                tokens=rec['tokens'], kinds=rec['kinds'], prompt_ids_sha256=rec['prompt_ids_sha256'],
                response_policy='artifact', response_sources=rec['response_sources'], prompt_id=prompt['prompt_id'],
                type=prompt['type'], draw=rec['draw'], seed=rec['seed'], round=round_tag,
                rl_selection=dict(kit=KIT_VERSION, round=round_tag, forced=rec['path'], r=sc['r'], c=sc['c'], n=sc['n'],
                                  answer=sc['answer'], gt_answer=str(prompt['gt_answer']), calls=len(rec['calls']),
                                  record_sha256=sha256_obj(rec)))


def held(prompt, rec, sc, round_tag, reason):
    return dict(prompt_id=prompt['prompt_id'], type=prompt['type'], round=round_tag, draw=rec['draw'],
                forced=rec['path'], answer=sc['answer'], r=sc['r'], n=sc['n'], reason=reason,
                response_sources=rec.get('response_sources'), record_sha256=sha256_obj(rec))


def select(prompts, groups, *, reward_cfg=None, program_types=(), validator=None, round_tag='r0', min_c=1.0,
           fallback_direct=False, quarantine_direct_majority=False, policy=None):
    """Returns dict of output lists plus a report. `groups`: {prompt_id: [records in draw order]}."""
    out = dict(vqa_rows=[], own_rows=[], barred=[], quarantine=[], refused=[], no_winner=[])
    kept = {}
    for prompt in prompts:
        recs = groups.get(prompt['prompt_id']) or []
        scored = score_group(prompt, recs, reward_cfg)
        best = winner(scored, min_c)
        if best is None:
            out['no_winner'].append(dict(prompt_id=prompt['prompt_id'], type=prompt['type'], draws=len(recs),
                                         right=sum(s['c'] >= min_c for s in scored), valid=sum(s['g'] for s in scored)))
            continue
        if best['path'] in ('head', 'recovery') and fallback_direct:
            best = winner(scored, min_c, 'direct') or best
        rec = recs[[r['draw'] for r in recs].index(best['draw'])]
        cell = kept.setdefault(prompt['type'], {}).setdefault(best['path'], 0)
        kept[prompt['type']][best['path']] = cell + 1
        if best['path'] in ('head', 'recovery'):  # a trace with printed responses trains as an own row
            reason = artifact_policy(rec, policy)
            if reason is not None:
                out['barred'].append(held(prompt, rec, best, round_tag, reason))
            elif quarantine_direct_majority and prompt['type'] not in program_types:
                out['quarantine'].append(held(prompt, rec, best, round_tag, 'head path on a direct-majority type'))
            else:
                out['own_rows'].append(own_row(prompt, rec, best, round_tag))
            continue
        row = vqa_row(prompt, rec, best, round_tag)
        try:
            if validator is not None:
                validator(row)
        except ValueError as exc:
            out['refused'].append(dict(prompt_id=prompt['prompt_id'], draw=rec['draw'], reason=str(exc),
                                       target=row['target']))
            continue
        out['vqa_rows'].append(row)
    report = dict(kit=KIT_VERSION, round=round_tag, prompts=len(prompts), min_c=min_c, fallback_direct=fallback_direct,
                  quarantine_direct_majority=quarantine_direct_majority, artifact_policy={**ARTIFACT_POLICY, **(policy or {})},
                  counts={k: len(v) for k, v in out.items()}, kept_by_type_path=kept,
                  reward_config_sha256=sha256_obj(reward_cfg or {}))
    return out, report


def tree_validator(tree):
    """The tree's own native admission for a VQA row. With frame pins in student_input (rows
    from the intake) the full `r2_contract.validate(row, 'vqa')` runs; a pre-intake row runs the
    same direct checks (shared grammar via `r2_grammar.validate_direct`, answer equals target,
    no program type offered as direct, numeric final answer on numeric types) and records that
    the frame-pin check is deferred to the intake."""
    if tree not in sys.path:
        sys.path.insert(0, tree)
    import re
    from student_pilot import r2_contract
    from student_pilot.r2_grammar import PROGRAM_TYPES, validate_direct

    def check(row):
        inputs = row['student_input']
        if inputs.get('frames'):
            r2_contract.validate(row, 'vqa')
            row['rl_selection']['admission'] = 'r2_contract.validate'
            return
        if row['question_type'] in PROGRAM_TYPES:
            raise ValueError('Program-type row offered as direct')
        answer = validate_direct(row['target'], inputs['question'], len(inputs['frame_indices']))
        answer = answer.removeprefix('<answer>').removesuffix('</answer>')
        if answer != str(row['answer']):
            raise ValueError('Answer differs from target')
        if row['question_type'] in ('room_size_estimation', 'object_size_estimation', 'camera_object_abs_distance',
                                    'object_counting') and not re.fullmatch(r'\d+(?:\.\d+)?', answer):
            raise ValueError('Numeric direct type needs a numeric final answer')
        row['rl_selection']['admission'] = 'r2_grammar.validate_direct; frame pins deferred to intake'
    return check, tuple(sorted(PROGRAM_TYPES))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--tree', required=True)
    ap.add_argument('--round', required=True)
    ap.add_argument('--reward-config')
    ap.add_argument('--floor', help='FLOOR.json from rlkit.floor; its n_min and n_ref enter the reward')
    ap.add_argument('--min-c', type=float, default=SELECT_DEFAULTS['min_c'])
    ap.add_argument('--fallback-direct', action='store_true')
    ap.add_argument('--quarantine-direct-majority', action='store_true')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    prompts = read_jsonl(a.prompts)
    reward_cfg = {**REWARD_DEFAULTS, **(json.loads(Path(a.reward_config).read_text()) if a.reward_config else {})}
    if a.floor:
        floor = json.loads(Path(a.floor).read_text())
        reward_cfg.update(n_min=floor['n_min'], n_ref=floor['n_ref'])
    head = json.loads((Path(a.run) / 'RUN_CONFIG.json').read_text())
    store = DrawStore(a.run, head['config'])
    groups = store.groups(prompts, head['config']['sampling']['draws'])
    validator, program_types = tree_validator(a.tree)
    out, report = select(prompts, groups, reward_cfg=reward_cfg, program_types=program_types, validator=validator,
                         round_tag=a.round, min_c=a.min_c, fallback_direct=a.fallback_direct,
                         quarantine_direct_majority=a.quarantine_direct_majority)
    report.update(run_config_hash=head['config_hash'])
    for name, rows in out.items():
        write_jsonl_atomic(Path(a.out) / f'{name}.jsonl', rows)
    atomic_write_json(Path(a.out) / 'SELECT_REPORT.json', report)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
