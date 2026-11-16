import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


COUNTS = {'pointing': 20239, 'pose': 194987, 'routing': 57136, 'vqa': 114904}
SCHEMA = 's1-donor-row-order-v1'
SCANNER_SOURCE_SHA256 = '5c1f4408ca88807dce33251eb638a786073e175cc32859317e929c425f02033a'


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def loads(text):
    return json.loads(text, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def accept(value, source_sha, config_pin, preparation_pin, counts):
    if (source_sha != SCANNER_SOURCE_SHA256
            or set(value) != {'schema', 'config', 'preparation', 'rows', 'scanner', 'resources'}
            or value['schema'] != SCHEMA or value['config'] != config_pin
            or value['preparation'] != preparation_pin
            or value['scanner'].get('schema') != 's1-readonly-row-scanner-v1'
            or value['scanner'].get('source_sha256') != source_sha
            or value['scanner'].get('counts') != counts
            or value['scanner'].get('readonly_immutable') is not True):
        raise ValueError('Scanner identity, donor pins, counts, or read-only contract differ')
    rows = value['rows']
    if set(rows) != {'schema', 'streams', 'sha256'} or rows['schema'] != 's1-ordered-row-content-v1':
        raise ValueError('Unknown ordered-row contract')
    streams = rows['streams']
    if (not isinstance(streams, list) or len(streams) != 4
            or [item.get('name') for item in streams] != list(counts)
            or value['scanner'].get('stream_order') != list(counts)
            or any(set(item) != {'name', 'count', 'sha256'} or type(item['count']) is not int
                   or item['count'] != counts[item['name']]
                   or not re.fullmatch('[0-9a-f]{64}', item['sha256']) for item in streams)):
        raise ValueError('Ordered stream inventory differs')
    payload = {key: part for key, part in rows.items() if key != 'sha256'}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                      allow_nan=False).encode()).hexdigest()
    pose = value['scanner'].get('pose_source_index_map')
    if (rows['sha256'] != digest or not isinstance(pose, dict) or pose.get('count') != counts['pose']
            or len(pose.get('sources', [])) != 2):
        raise ValueError('Row digest or two-source pose map differs')
    limits = value['resources']
    if (not 0 < limits['cpus'] <= 2 or not 0 < limits['peak_rss_bytes'] <= 4*2**30
            or limits['address_space_limit_bytes'] != 4*2**30
            or limits['rows'] != sum(counts.values()) or not 0 <= limits['seconds'] < 900):
        raise ValueError('Scanner bounds differ')
    return {**{key: value[key] for key in ('schema', 'config', 'preparation', 'rows')},
            'scanner_source_sha256': source_sha}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--scanner-source', required=True)
    parser.add_argument('--config-pin', required=True)
    parser.add_argument('--preparation-pin', required=True)
    args = parser.parse_args()
    try:
        path = Path(args.input)
        if path.stat().st_size > 65536:
            raise ValueError('Scanner output is not a small JSON document')
        result = accept(loads(path.read_text()), hashlib.sha256(Path(args.scanner_source).read_bytes()).hexdigest(),
                        loads(args.config_pin), loads(args.preparation_pin), COUNTS)
        print(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False))
        return 0
    except Exception as error:
        print(json.dumps(dict(schema='s1-row-scan-acceptance-refusal-v1', status='REFUSED', reason=str(error))))
        return 2


if __name__ == '__main__':
    sys.exit(main())
