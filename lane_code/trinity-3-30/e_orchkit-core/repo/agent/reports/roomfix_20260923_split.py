"""split_trainer.json for the uncapped Set-B-recipe mix.

Reproduces claude_gtmeasure_mix2_20260922T1855Z/emit_split_trainer.py (same schema, same trainer
checkout b084aaf, same load_inherited_record + make_inherited_split round trip) for one set, and
adds the inheritance check against the PUBLISHED Set B record: the new rows are fed through
make_inherited_split with S/mix_v25_gtm2_r050_20260922/split_trainer.json as the inherited
record, and the derived sides must equal the mixer's sides. hashed_group_count is recorded for
both passes.
"""
import json, sys
from pathlib import Path

CHECKOUT = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_onethinker_v241_launch_20260921T0015Z/work_checkout_b084aaf')
WORKTREE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CHECKOUT))
sys.path.insert(0, str(WORKTREE))

from student_pilot.common import digest_json                                     # noqa: E402
from student_pilot.split import WHOLE_SCENE_GROUP_POLICY, physical_group         # noqa: E402
from student_pilot.provisional import load_inherited_record                      # noqa: E402
from student_pilot.split import make_inherited_split                             # noqa: E402
from tools.gtmeasure.io import pin, read_json, read_jsonl, write_json            # noqa: E402

PILOT = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918')
MIX = PILOT / 'mix_v25_uncapped_gtm2_r050_roomfix_20260923'
SETB_RECORD = PILOT / 'mix_v25_uncapped_gtm2_r050_20260923' / 'split_trainer.json'
SETB_SHA = 'd0dd515927794b234ea4b794c793b9506fafa9355f41817f7e75e5bfea3beede'


def sides_of(rows):
    return (sorted({f'{r["dataset"]}/{r["scene"]}' for r in rows}),
            sorted({physical_group(r['dataset'], r['scene']) for r in rows}))


def pin_for(path):
    spec = pin(path)
    return {'path': spec['path'], 'sha256': spec['sha256']}


def main():
    mix = MIX
    published = read_json(mix / 'split.json')
    train = list(read_jsonl(mix / 'train.jsonl'))
    heldout = list(read_jsonl(mix / 'heldout.jsonl'))
    if [r['qid'] for r in train] != published['train_qids'] or [r['qid'] for r in heldout] != published['heldout_qids']:
        raise ValueError('row files disagree with the published split qids')
    rows = [{'qid': r['qid'], 'dataset': r['dataset'], 'scene': r['scene'], 'category': r['category']}
            for r in [*train, *heldout]]
    want_train, want_held = sorted(r['qid'] for r in train), sorted(r['qid'] for r in heldout)

    # 1. inheritance from the published Set B record
    setb_spec = pin_for(SETB_RECORD)
    if setb_spec['sha256'] != SETB_SHA:
        raise ValueError('Set B split_trainer.json sha256 differs from the published pin')
    setb = load_inherited_record(setb_spec)
    from_b = make_inherited_split(rows, rows, setb, seed=17, heldout_fraction=0.1)
    b_agrees = from_b['train_candidate_qids'] == want_train and from_b['heldout_qids'] == want_held
    b_moved_to_train = sorted(set(from_b['train_candidate_qids']) & set(want_held))
    b_moved_to_held = sorted(set(from_b['heldout_qids']) & set(want_train))

    if not b_agrees:
        raise ValueError('inherited split changed a scene side')

    # 2. emit this set's own record (Set B schema), verified by the same round trip
    train_scenes, train_groups = sides_of(train)
    heldout_scenes, heldout_groups = sides_of(heldout)
    if set(train_groups) & set(heldout_groups):
        raise ValueError('a physical group would land on both sides under the trainer grouping')
    if set(train_scenes) & set(heldout_scenes):
        raise ValueError('a scene would land on both sides')
    source = pin(mix / 'split.json')
    content = {
        'schema': 'provisional-whole-scene-split-v1',
        'group_policy': WHOLE_SCENE_GROUP_POLICY,
        'seed': 17,
        'heldout_fraction_of_groups': 0.1,
        'selection_uses_correctness': False,
        'infrastructure_only': False,
        'benchmark_improvement_claim': False,
        'benchmark_trained_diagnostic': True,
        'score_nomination_allowed': False,
        'result_status': 'diagnostic, provisional',
        'provisional_diagnostic': 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW',
        'donor_group_count': len(set(train_groups) | set(heldout_groups)),
        'donor_scene_count': len(set(train_scenes) | set(heldout_scenes)),
        'train_group_ids': train_groups,
        'heldout_group_ids': heldout_groups,
        'train_scenes': train_scenes,
        'heldout_scenes': heldout_scenes,
        'train_candidate_qids': want_train,
        'heldout_qids': want_held,
        'source_split': source,
        'source_split_schema': published['schema'],
        'inherited_from': {'path': setb_spec['path'], 'sha256': setb_spec['sha256'],
                           'hashed_group_count': from_b['hashed_group_count'],
                           'hashed_group_ids': from_b['hashed_group_ids'],
                           'reproduces_mixer_sides': b_agrees},
        'note': ('Re-expression of the mixer split.json pinned in source_split, in the schema the trainer '
                 'accepts, every scene named on one list. inherited_from records the check that '
                 'make_inherited_split over these rows with the published Set B record yields the same sides.'),
    }
    record = {**content, 'provenance': {'config_sha256': digest_json(content),
                                        'source_split_sha256': source['sha256'],
                                        'emitted_by': 'agent/reports/roomfix_20260923_split.py'}}
    out = mix / 'split_trainer.json'
    if out.exists():
        raise FileExistsError(str(out))
    write_json(out, record)
    loaded = load_inherited_record(pin_for(out))
    derived = make_inherited_split(rows, rows, loaded, seed=17, heldout_fraction=0.1)
    agrees = derived['train_candidate_qids'] == want_train and derived['heldout_qids'] == want_held
    if not agrees:
        raise ValueError('trainer-inherited split does not reproduce the published sides')
    result = {'path': str(out), 'sha256': pin(out)['sha256'], 'schema': content['schema'],
              'train_qids': len(want_train), 'heldout_qids': len(want_held),
              'train_scenes': len(train_scenes), 'heldout_scenes': len(heldout_scenes),
              'train_groups': len(train_groups), 'heldout_groups': len(heldout_groups),
              'source_split_sha256': source['sha256'],
              'hashed_group_count': derived['hashed_group_count'],
              'trainer_reproduces_published_sides': agrees,
              'setb_inheritance': {'hashed_group_count': from_b['hashed_group_count'],
                                   'hashed_group_ids': from_b['hashed_group_ids'],
                                   'inherited_group_count': from_b['inherited_group_count'],
                                   'reproduces_mixer_sides': b_agrees,
                                   'mixer_heldout_but_setb_train': len(b_moved_to_train),
                                   'mixer_train_but_setb_heldout': len(b_moved_to_held)}}
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
