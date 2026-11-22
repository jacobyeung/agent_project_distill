"""Decode the encoded causes a CPU check leaves (1.log lines and REHEARSAL.json evidence) into text."""
import base64, gzip, json, sys
from pathlib import Path


def walk(value, path=''):
    if isinstance(value, dict):
        if 'gz64' in value:
            yield path, gzip.decompress(base64.b64decode(value['gz64'])).decode('utf-8', 'replace')
        for k, v in value.items():
            yield from walk(v, path + '/' + str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, path + '/' + str(i))


for name in sys.argv[1:]:
    text = Path(name).read_text(errors='replace')
    docs = []
    try:
        docs = [json.loads(text)]
    except ValueError:
        for line in text.splitlines():
            try:
                docs.append(json.loads(line))
            except ValueError:
                pass
    for doc in docs:
        for where, body in walk(doc):
            print('=== %s %s\n%s' % (name, where, body))
