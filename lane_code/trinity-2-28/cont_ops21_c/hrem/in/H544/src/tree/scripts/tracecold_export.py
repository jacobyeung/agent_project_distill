import argparse
from pathlib import Path

from scripts.tracecold_build_rows import DATA_READY, native_export
from student_pilot.trace_io import canonical, load, pin, require, rows, save, verify
from student_pilot.trace_targets import lint_row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rows-ready', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve every native export epoch')
    ready_pin = pin(args.rows_ready)
    ready = load(args.rows_ready)
    from student_pilot.storage import code_provenance
    data = load(verify(DATA_READY))
    provenance = code_provenance({'rows_ready': ready_pin, 'renderer': ready['linter']})
    exported = {}
    for arm in ('TR', 'AO'):
        training = list(rows(verify(ready['arms'][arm]['training'])))
        heldout = list(rows(verify(ready['arms'][arm]['heldout_support_not_trained'])))
        require([row['qid'] for row in training] == ready['training_order'] and len(training) == 6000,
                'The frozen training order changed')
        require([row['qid'] for row in heldout] == ready['heldout_order'] and len(heldout) == 269,
                'The frozen descriptive holdout changed')
        for row in training + heldout:
            lint_row(row, arm)
        exported[arm] = native_export(training + heldout, arm, args.output, provenance['commit'])
    require(ready_pin == pin(args.rows_ready), 'Row authority changed during export')
    result = {'schema': 'tracecold-native-export-v1', 'status': 'EXPORTED_NOT_ADMITTED', 'rows_ready': ready_pin,
              'provenance': provenance, 'GT_source_commit': data['source_geometry_commit'],
              'candidate_indices': exported, 'training_rows_per_arm': 6000, 'heldout_rows_not_trained': 269,
              'warm_start': False, 'code': pin(__file__)}
    print(canonical({'output': save(args.output / 'EXPORTED.json', result)}), flush=True)


if __name__ == '__main__':
    main()
