import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'donor_row_scanner_07ca49df/scan_donor_rows.py'
SOURCE_SHA = '5c1f4408ca88807dce33251eb638a786073e175cc32859317e929c425f02033a'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
spec = importlib.util.spec_from_file_location('frozen_fixture_scanner', SOURCE)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


def capture_fixture_attestation(config_pin):
    path = Path(config_pin['path'])
    cfg = scanner.loads(path.read_bytes())
    receipt = scanner.loads(Path(cfg['preparation']['path']).read_bytes())
    logical = {'path': '/fixture/inputs/' + path.name, 'sha256': config_pin['sha256']}
    worker = scanner.Scanner(path.parent, path.parent, logical)
    raw = worker.snapshot({name: value['count'] for name, value in receipt['streams'].items()})
    return {**{key: raw[key] for key in ('schema', 'config', 'preparation', 'rows')},
            'scanner_source_sha256': raw['scanner']['source_sha256']}
