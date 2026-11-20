#!/usr/bin/env python3
"""Read only six named published files, serially paced, to check alias safety.

The corpus owner runs this on trinity-3-30 after scheduling the shared I/O.
Exit 0 proves no devrows: item IDs in these files; 1 finds such IDs; 2 means
the scan is incomplete or the file identities/counts do not match the snapshot.
This does not certify duplicate report scores or native-return integrity.
"""
import argparse
import gzip
import io
import json
from pathlib import Path
import sys
import time
import zlib


# From the supplied published INDEX snapshot, SHA256
# bdf2d9cef181e5d8ca33775bf2793ef8ced115d97b0dd25fae8495c3bd93944c.
EXPECTED_COUNTS = {
    '17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936': 3994,
    '359fcc3c_s100_devS1R0facing_direct_af35386aa3e': 3994,
    '359fcc3c_s200_devS1facing_direct_a4cadd8934b': 1825,
    '673bc60f_s100_devS1R0_direct_a5d2d909067': 3120,
    '673bc60f_s200_devS1R0_direct_a8102c3207b': 3120,
    '673bc60f_s200_facing_direct_a2e46c0504e': 300,
}
BYTES_PER_SECOND = 1024 * 1024
CHUNK = 64 * 1024
MAX_LINE = 128 * 1024 * 1024


class PacedReader(io.RawIOBase):
    """Sleep before every bounded, unbuffered physical read; never catch up."""
    def __init__(self, stream):
        self.stream = stream
        self.bytes_read = 0

    def readable(self):
        return True

    def readinto(self, buffer):
        size = min(len(buffer), CHUNK)
        if not size:
            return 0
        time.sleep(size / BYTES_PER_SECOND)
        data = self.stream.read(size)
        buffer[:len(data)] = data
        self.bytes_read += len(data)
        return len(data)


def scan(root):
    total_items = total_matches = total_bytes = 0
    for read_id, expected in EXPECTED_COUNTS.items():
        path = Path(root) / 'reads' / (read_id + '.jsonl.gz')
        print('SCAN ' + str(path), flush=True)
        count = matches = 0
        # No glob, directory walk, INDEX read, or other corpus files are opened.
        with path.open('rb', buffering=0) as raw:
            paced = PacedReader(raw)
            with io.BufferedReader(paced, buffer_size=CHUNK) as buffered:
                with gzip.GzipFile(fileobj=buffered, mode='rb') as stream:
                    while True:
                        line = stream.readline(MAX_LINE + 1)
                        if not line:
                            break
                        if len(line) > MAX_LINE:
                            raise ValueError('Oversized row in ' + str(path))
                        row = json.loads(line)
                        if (not isinstance(row, dict) or row.get('read_id') != read_id
                                or not isinstance(row.get('item_id'), str)):
                            raise ValueError('Invalid read_id/item_id in ' + str(path))
                        count += 1
                        matches += row['item_id'].startswith('devrows:')
        if count != expected:
            raise ValueError('%s: %d items != expected %d' % (read_id, count, expected))
        total_items += count
        total_matches += matches
        total_bytes += paced.bytes_read
        print('%s: items=%d devrows_item_ids=%d compressed_bytes=%d' %
              (read_id, count, matches, paced.bytes_read), flush=True)
    print('COMPLETE: files=%d items=%d devrows_item_ids=%d compressed_bytes=%d' %
          (len(EXPECTED_COUNTS), total_items, total_matches, total_bytes), flush=True)
    return 1 if total_matches else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus-root', required=True,
                        help='Explicit corpus root; the script opens only the six named reads.')
    args = parser.parse_args(argv)
    try:
        return scan(args.corpus_root)
    except (OSError, EOFError, ValueError, zlib.error) as error:
        print('INCOMPLETE: ' + str(error), file=sys.stderr, flush=True)
        return 2


if __name__ == '__main__':
    sys.exit(main())
