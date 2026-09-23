import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path

from .blocking import benchmark_blocking
from .conventions import MEASURES, structure_conventions
from .io import canonical, digest, pin, read_json, source_commit, verify_pin
from .mix import measurement_rows
from .questions import rewrite_room_row
from .room_labels import POLICY, RoomLabelDeferred, RoomLabels
from .split import load_split
from .swarm import common_input_digest, require, write_new


def corrected_conventions(original):
    result = copy.deepcopy(original)
    if 'structure_v2' in result:
        result = structure_conventions(result, 'v2')
    result.setdefault('measurements', {})['gtm_room_size'] = {
        **result.get('measurements', {}).get('gtm_room_size', {}), **MEASURES['gtm_room_size'],
        'value_authority': result['authorities']['vsi']}
    result['room_label_policy'] = POLICY
    return result


class RoomRepair:
    def __init__(self, manifest_pin):
        manifest_path = verify_pin(manifest_pin)
        self.sides, self.manifest, self.split_record, _ = measurement_rows(manifest_path.parent)
        self.conventions = corrected_conventions(read_json(verify_pin(self.manifest['artifacts']['CONVENTIONS.json'])))
        expected = self.manifest['inputs']['wording_authorities']['vsi']
        require(self.conventions['authorities']['vsi'] == expected, 'room_label_foreign_authority')
        self.policy = load_split(verify_pin(self.manifest['inputs']['split']))
        _, self.blocked = benchmark_blocking(self.manifest['benchmark_blocking'])
        self.train = {row['qid']: row for row in self.sides['train']}
        self.heldout = {row['qid'] for row in self.sides['heldout']}
        require(set(self.train) == set(self.split_record['train_qids']) and self.heldout == set(self.split_record['heldout_qids']),
                'room_repair_published_membership')
        identities = {(row['dataset'], row['scene']) for row in self.sides['train'] if row['family'] == 'gtm_room_size'}
        self.labels = RoomLabels(expected, identities, self.policy, self.blocked)
        self.config = {'schema': 'gtmeasure-room-repair-config-v1', 'room_label_policy': POLICY,
                       'source_manifest': manifest_pin, 'conventions_sha256': digest(self.conventions),
                       'source_label_authority': expected, 'selection': 'retain qids and inputs; repair only training room rows'}
        self.config_sha = digest(self.config)

    def rewrite(self, qid, commit):
        if qid not in self.train or qid in self.heldout:
            raise RoomLabelDeferred('room_label_not_published_training_qid')
        return rewrite_room_row(self.train[qid], self.conventions, self.labels, commit=commit, config_sha=self.config_sha,
                                structure=self.manifest['config'].get('structure', 'v1'))


def audit_common(common_done, commit):
    done = read_json(common_done)
    require(done.get('passed') is True and done.get('rows') == 1000, 'room_repair_common_admission')
    membership = read_json(verify_pin(done['membership']))
    verify_pin(done['split'])
    repair = RoomRepair(membership['gtm_manifest'])
    selected = [row for row in membership['rows'] if row['family'] == 'gtm_room_size']
    require(len(membership['rows']) == 1000 and len(selected) == 100, 'room_repair_fixed_membership')
    output, deferred = [], []
    for record in selected:
        before = repair.train[record['qid']]
        require(all(record[key] == before[key] for key in ('qid', 'dataset', 'scene', 'family'))
                and record['answer'] == before['ground_truth']['answer']
                and record['input_sha256'] == common_input_digest(before['student_input'])
                and record['gtm_source_path'] == repair.manifest['artifacts']['train.jsonl']['path'], 'room_repair_source_identity')
        try:
            after = repair.rewrite(record['qid'], commit)
        except ValueError as error:
            deferred.append({'qid': record['qid'], 'reason': str(error)})
            continue
        require(before['student_input'] == after['student_input'] and before['qid'] == after['qid'], 'room_repair_input_drift')
        label = after['provenance']['room_label']
        output.append({'qid': before['qid'], 'dataset': before['dataset'], 'scene': before['scene'],
                       'old_answer': before['ground_truth']['answer'], 'new_answer': after['ground_truth']['answer'],
                       'units': after['ground_truth']['units'], 'old_value_si': before['ground_truth']['measurements'][0]['value_si'],
                       'new_value_si': after['ground_truth']['measurements'][0]['value_si'], 'source_label': label,
                       'old_row_canonical_sha256': digest(before), 'new_row_canonical_sha256': digest(after),
                       'old_observations': before['observations'], 'new_observations': after['observations']})
    return {'schema': 'gtmeasure-room-repair-audit-v1', 'checked_at': datetime.now(timezone.utc).isoformat(),
            'commit': commit, 'common_done': pin(common_done), 'membership': done['membership'], 'split': done['split'],
            'config': repair.config, 'config_sha256': repair.config_sha,
            'attempted': len(selected), 'admitted': len(output), 'deferred': deferred, 'rows': output,
            'training_launched': False, 'common_v2_frozen': False,
            'scope': 'Authenticated CPU-only room-supervision replay; this report is not an admission or training gate.'}


def main():
    parser = argparse.ArgumentParser(description='Authenticate and replay the room-only correction without changing a frozen corpus.')
    parser.add_argument('--common-done', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(args.output.resolve().is_relative_to('/data2'), 'room_repair_output_root')
    result = audit_common(args.common_done, source_commit())
    write_new(args.output, (canonical(result) + '\n').encode())
    print(canonical({key: result[key] for key in ('commit', 'attempted', 'admitted', 'deferred')}), flush=True)
    for row in result['rows'][:20]:
        print(canonical({key: row[key] for key in ('qid', 'old_answer', 'new_answer', 'units', 'new_value_si')}), flush=True)
    return 0 if result['admitted'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
