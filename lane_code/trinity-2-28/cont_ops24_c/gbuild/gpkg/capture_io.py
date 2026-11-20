"""Authenticate raw capture bytes, then stream complete gzip JSONL records."""
import hashlib
import json
from pathlib import Path
import zlib


class Records:
    def __init__(self, path, receipt):
        self.path = Path(path)
        if not isinstance(receipt, dict):
            receipt = json.loads(Path(receipt).read_text())
        expected = receipt.get('sha256', receipt.get('capture_sha256'))
        if not expected:
            raise ValueError('capture raw SHA256 is required')
        with self.path.open('rb') as f:
            actual = hashlib.file_digest(f, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError('capture raw SHA256 differs')
        size = self.path.stat().st_size
        expected_size = receipt.get('bytes', receipt.get('capture_bytes'))
        if expected_size is not None and expected_size != size:
            raise ValueError('capture raw byte count differs')
        self.report = dict(raw_sha256=actual, raw_bytes=size, sha256_verified=True,
                           salvaged=False, records=0, discarded_partial_line_bytes=0)

    def __iter__(self):
        codec = zlib.decompressobj(wbits=16+15)
        pending = b''
        with self.path.open('rb') as f:
            while True:
                chunk = f.read(1024*1024)
                if not chunk:
                    break
                if codec.eof:
                    raise ValueError('unexpected bytes after gzip stream')
                # Bound each decompression allocation; a record may span chunks.
                while chunk:
                    data = codec.decompress(chunk, 1024*1024)
                    chunk = codec.unconsumed_tail
                    pending += data
                    lines = pending.split(b'\n')
                    pending = lines.pop()
                    for line in lines:
                        row = json.loads(line)
                        self.report['records'] += 1
                        yield row
                if codec.unused_data:
                    raise ValueError('unexpected bytes after gzip stream')
        self.report.update(salvaged=not codec.eof, discarded_partial_line_bytes=len(pending))
        if codec.eof and pending:
            raise ValueError('complete capture lacks final JSONL newline')
