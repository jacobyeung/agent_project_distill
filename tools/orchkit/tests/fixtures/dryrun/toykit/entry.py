"""Toy batch entry: fetch one object, read CONFIG, prepare every item, write a return."""
import json
import os
import subprocess
import sys

import helper


def main(config_path):
    with open(config_path) as handle:
        config = json.load(handle)
    spec = config['spec']
    os.makedirs(spec['work_dir'], exist_ok=True)
    subprocess.check_call(['gsutil', 'cp', spec['object'] + '#' + spec['generation'],
                           spec['items_path']])
    print('STAGE stage', flush=True)
    items = helper.load_items(spec['items_path'], config['n_items'])
    print('STAGE admit', flush=True)
    for item in items:
        helper.prepare(item, spec['work_dir'])
        print('ITEM %s' % item['id'], flush=True)
    print('STAGE first_batch', flush=True)
    helper.write_return(spec['work_dir'], spec['return_dir'], len(items))
    print('STAGE return', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
