import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from .p3_provenance import file_pin, pinned


def row_keys(row):
    values = [row.get("row_key"), row.get("qid")]
    for field in ("pointing", "grounding", "provenance"):
        if isinstance(row.get(field), dict):
            values.append(row[field].get("row_key"))
    values.extend(row.get("label_row_keys", []))
    return {str(value) for value in values if value is not None}


class Removals:
    def __init__(self, files=(), *, stream=None):
        self.stream = stream
        self.files = [value if isinstance(value, dict) else file_pin(value) for value in files]
        self.keys = []
        self.source_counts = []
        self.extent_only = set()
        self.removed = [0] * len(self.files)
        self.matches = [0] * len(self.files)
        self.matched_keys = [set() for _ in self.files]
        for value in self.files:
            if 'role' in value or 'stream' in value:
                from .r1_launch22 import STREAMS
                if (set(value) != {'path', 'sha256', 'role', 'stream'}
                        or value.get('role') != 'protected_rooms' or value.get('stream') not in STREAMS):
                    raise ValueError('R1_NAMING_REMOVAL_ORDER')
            elif set(value) - {'path', 'sha256', 'defects'}:
                raise ValueError("Unknown REMOVE-list rule")
            pin = {key: value[key] for key in ('path', 'sha256')}
            from .r1_launch22 import NAMING_REMOVE, naming_rows
            rows = (naming_rows(pin) if pin['sha256'] == NAMING_REMOVE else
                    [json.loads(line) for line in pinned(pin).read_text().splitlines() if line.strip()])
            if any(not isinstance(row.get("row_key"), str) or not row["row_key"] for row in rows):
                raise ValueError("REMOVE lists require explicit nonempty row_key strings")
            self.source_counts.append(len(rows))
            if 'defects' in value:
                defects = value['defects']
                if (not isinstance(defects, list) or not defects
                        or not set(defects) <= {'identity', 'absent', 'merged', 'extent'}):
                    raise ValueError("Invalid REMOVE-list defect restriction")
                if any(not set(row.get('defect', '').split('|')) <=
                       {'identity', 'absent', 'merged', 'extent'} for row in rows):
                    raise ValueError("Restricted REMOVE list has an unknown defect")
                self.extent_only.update(row['row_key'] for row in rows if row['defect'] == 'extent'
                                        and 'extent' not in defects)
                rows = [row for row in rows if set(row['defect'].split('|')) & set(defects)]
            self.keys.append({row["row_key"] for row in rows})

    def match(self, row, stream=None):
        stream = self.stream if stream is None else stream
        if any(p.get('role') == 'protected_rooms' for p in self.files):
            from .r1_launch22 import STREAMS
            if stream not in STREAMS:
                raise ValueError('R1_PROTECTED_REMOVAL_STREAM_REQUIRED')
        keys = row_keys(row)
        return [i for i, removed in enumerate(self.keys) if keys & removed
                and (self.files[i].get('role') != 'protected_rooms' or self.files[i]['stream'] == stream)]

    def keep(self, row, stream=None):
        matched = self.match(row, stream)
        for index in matched:
            self.matches[index] += 1
            self.matched_keys[index].update(row_keys(row) & self.keys[index])
        if matched:
            self.removed[matched[0]] += 1
        return not matched

    def assert_clean(self, row, stream=None):
        matched = self.match(row, stream)
        if matched:
            raise ValueError(f"REMOVE-listed row remains in admitted receipt: {sorted(row_keys(row))}; files={matched}")

    def verify_streams(self, streams):
        if not self.files:
            return
        from .s1_exclusions import selection

        def keep(row, source):
            self.assert_clean(row, name)
            return True

        rule = SimpleNamespace(counts=lambda source: None, expect=lambda source, rows, population: None, keep=keep)
        for name, stream in streams.items():
            selection(name, stream, rule)

    def report(self):
        values = [dict(file=value, source_listed=source_count, listed=len(keys), removed=count, matched=matched,
                       matched_unique_keys=len(seen), unmatched_listed_keys=len(keys)-len(seen),
                       retained_by_filter=source_count-len(keys))
                  for value, keys, count, matched, seen, source_count
                  in zip(self.files, self.keys, self.removed, self.matches, self.matched_keys, self.source_counts, strict=True)]
        for value in values:
            print(json.dumps(dict(remove_list=value)), flush=True)
        return values


def filter_jsonl(source, output, files, *, stream=None):
    removals = Removals(files, stream=stream)
    source = pinned(source) if isinstance(source, dict) else Path(source)
    output = Path(output)
    kept = 0
    with source.open() as stream, output.open("x") as target:
        for line in stream:
            row = json.loads(line)
            if removals.keep(row):
                target.write(json.dumps(row, sort_keys=True) + "\n")
                kept += 1
    return dict(rows=file_pin(output), kept=kept, removals=removals.report())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--remove-files", nargs="+", required=True)
    args = parser.parse_args()
    print(json.dumps(filter_jsonl(args.input, args.output, args.remove_files), indent=2))


if __name__ == "__main__":
    main()
