"""Toy kit helpers: item loading, per-item preparation and the return file."""
import json
import os


def load_items(path, count):
    with open(path) as handle:
        items = json.load(handle)
    if len(items) != count:
        raise ValueError('the object holds %d items; the config says %d' % (len(items), count))  # never-run: error_path the config and the object disagree
    return items


def prepare(item, work_dir):
    with open(os.path.join(work_dir, '%s.json' % item['id']), 'w') as handle:
        json.dump(item, handle, sort_keys=True)


def write_return(work_dir, return_dir, count):
    with open(os.path.join(return_dir, 'RETURN.json'), 'w') as handle:
        json.dump({'prepared': count, 'files': sorted(os.listdir(work_dir))}, handle, sort_keys=True)
