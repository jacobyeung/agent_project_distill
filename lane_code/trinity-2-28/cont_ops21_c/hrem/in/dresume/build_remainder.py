"""Build a fresh D remainder delivery; do not place, fill, or submit it."""
import argparse
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'dbuild'))
from build_d import build


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('stage','source','source-sha','items','binding','time'):
        p.add_argument('--'+name,required=True)
    a=p.parse_args()
    stage=Path(a.stage)
    if stage.exists():
        raise ValueError('Use a fresh stage directory')
    manifest=json.loads(Path(a.items).read_text())
    if 'remainder' not in manifest:
        raise ValueError('Expected authenticated remainder manifest')
    report=build(stage,Path(a.source),a.source_sha,Path(a.items),Path(a.binding),
                 HERE/'dbuild/TIMING_D.json',a.time)
    # Preserve all helpers needed by the existing placement/fill protocol.
    for name in ('place_fill_d.py','dryres_d.py','build_support.py','make_items_d.py','o_cpu_D.sh','o_sub_D.sh'):
        (stage/name).write_bytes((HERE/'dbuild'/name).read_bytes())
    (stage/'binding.json').write_bytes(Path(a.binding).read_bytes())
    (stage/'items.json').write_bytes(Path(a.items).read_bytes())
    print(json.dumps(dict(stage=str(stage),package=report['package'],count=manifest['count'],submitted=False)))


if __name__=='__main__':
    main()
