import argparse
from pathlib import Path
import tempfile

from stage_lib import (
    EPOCHS, STUDENT, dataset_identity, freeze_config, load_student_config,
    validate_config, verify_identity,
)


FIXTURES = {
    'setH': (9232, 7684, 1548, {
        'candidate_index.jsonl': '5797eac24b659eb9c5ac7f41242f842a345e231b5cd7ed7135758cc85de97cca',
        'split_trainer.json': 'eec29d981c5c30b6217c72938bfbb1c0cbd13842ff651767a2c657125092cb27',
    }),
    'fullpool': (29399, 25164, 4235, {
        'candidate_index.jsonl': 'b0658afc8c5a7439277985e59a13429d31b64dcbfb1f7f2087e49bb753456446',
        'split_trainer.json': '46d0d91058623f5031b2f548afb14bcc26c2cb3e44664b48edba767fdfdf7f70',
    }),
}


def check(frozen_root):
    for variant, epochs in EPOCHS.items():
        here = frozen_root / variant
        freeze_config(variant, here)
        config = validate_config(variant, load_student_config(here, STUDENT))
        assert (config['epochs'], config['world_size'], config['effective_batch_size']) == (epochs, 4, 32)
        identity = dataset_identity(variant)
        total, train, heldout, hashes = FIXTURES['fullpool' if variant == 'fullpool' else 'setH']
        assert identity['rows'] == {'total': total, 'train': train, 'heldout': heldout}
        assert identity['sha256'] == hashes
        assert Path(identity['split_record']).name == 'split_trainer.json'
        verify_identity(identity, hashes, total)
        invalid = [({**hashes, filename: '0' * 64}, total) for filename in hashes]
        invalid.append((hashes, total - 1))
        for changed_hashes, changed_rows in invalid:
            try:
                verify_identity(identity, changed_hashes, changed_rows)
            except ValueError:
                continue
            raise AssertionError('Identity check accepted a changed hash or row count')
        print(f'PASS {variant}: student={STUDENT}, epochs={epochs}, world_size=4, effective_batch_size=32, rows={total}')
    print('PASS: 3 configs; 6 literal SHA256 checks; 9 negative identity checks.')
    print('Retained frozen config aliases: ' + str(frozen_root))
    print('CPU only: no model load, Orchard file access, or scheduler calls.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frozen-root', type=Path)
    args = parser.parse_args()
    root = args.frozen_root or Path(tempfile.mkdtemp(prefix='qwen27b_ao_dry_run_'))
    check(root)


if __name__ == '__main__':
    main()
