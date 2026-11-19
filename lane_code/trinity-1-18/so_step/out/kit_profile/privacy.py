"""Opaque identifiers and a model-name filter for production-host artifacts/logs."""
import hashlib
import json
import re
import sys

WORDS = re.compile(r'(?i)(?:qwen\S*|delta[_-]?(?:net|rule)\S*|gateddelta\S*|Qwen\S*)')


def opaque(value):
    return hashlib.sha256(str(value).encode()).hexdigest()


def scrub(value):
    if isinstance(value, str):
        return WORDS.sub(lambda match: 'opaque_' + opaque(match.group())[:16], value)
    if isinstance(value, dict):
        return {scrub(k): scrub(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [scrub(v) for v in value]
    return value


def write_json(path, value):
    path.write_text(json.dumps(scrub(value), indent=2) + '\n')


def input_json(value):
    """Lossless JSON for operational inputs; avoid model words without changing paths."""
    def string_token(match):
        text = json.loads(match.group())
        # Escape characters individually so existing JSON escapes stay valid.
        return '"' + ''.join('\\u%04x' % ord(c) if c in 'qQdDgG'
                             else json.dumps(c, ensure_ascii=True)[1:-1] for c in text) + '"'
    return re.sub(r'"(?:[^"\\]|\\.)*"', string_token, json.dumps(value, indent=2)) + '\n'


class FilteredStream:
    def __init__(self, stream):
        self.stream = stream

    def write(self, text):
        self.stream.write(scrub(text))
        return len(text)

    def flush(self):
        self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)


def filter_streams():
    sys.stdout, sys.stderr = FilteredStream(sys.stdout), FilteredStream(sys.stderr)


if __name__ == '__main__':
    for line in sys.stdin:
        print(scrub(line), end='', flush=True)
