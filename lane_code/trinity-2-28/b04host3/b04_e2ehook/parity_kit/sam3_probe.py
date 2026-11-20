"""Import SAM3 dependencies without constructing or running a model."""
import argparse
import importlib
import json
from pathlib import Path
import sys

from parity_kit.common import TREE, install


def probe(source_root, checkpoint, tree=TREE):
    install(tree)
    source = Path(source_root).resolve()
    sys.path.insert(0, str(source))
    report = dict(source_root=str(source), source_exists=(source / 'sam3').is_dir(),
                  checkpoint=str(Path(checkpoint).resolve()),
                  checkpoint_exists=Path(checkpoint).is_file(), missing_packages=[], import_errors={}, imported=[])
    for name in ('student_pilot.sam3_tower', 'sam3.model_builder', 'sam3.model.sam3_image_processor'):
        try:
            module = importlib.import_module(name)
            if name == 'student_pilot.sam3_tower':
                getattr(module, 'Sam3Tower')
            elif not Path(module.__file__).resolve().is_relative_to(source):
                raise ValueError('SAM3 imported from outside the requested source root')
            report['imported'].append(name)
        except ModuleNotFoundError as e:
            report['missing_packages'].append(e.name)
            report['import_errors'][name] = str(e)
        except Exception as e:
            report['import_errors'][name] = type(e).__name__ + ': ' + str(e)
    report['missing_packages'] = sorted(set(report['missing_packages']))
    report['ready_to_load'] = report['source_exists'] and report['checkpoint_exists'] and not report['import_errors']
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', required=True)
    p.add_argument('--checkpoint', required=True)
    p.add_argument('--tree', default=str(TREE))
    a = p.parse_args()
    print(json.dumps(probe(a.source_root, a.checkpoint, a.tree), indent=2))


if __name__ == '__main__':
    main()
