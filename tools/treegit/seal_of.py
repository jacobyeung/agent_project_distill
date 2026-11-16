"""seal_of.py --code CODE_ROOT DIR [DIR ...]: print one JSON object with the trainer seal of each DIR.

The seal is computed by the trainer tree's own code: ``student_pilot/source_seal.inventory`` and
``student_pilot/p3_provenance.digest`` loaded from CODE_ROOT, never a reimplementation. The package
``student_pilot`` is registered without running its ``__init__.py``, and no bytecode is written.
Run under the trainer interpreter (p1cpu, Python 3.12) with ``-I -B``.
Output: {"code_root": ..., "trees": {DIR: {"tree_sha256": hex, "files": {rel: sha256}}}} or, for a
tree the seal code refuses, {"error": text} in place of the two fields. Exit 0 when every tree sealed.
"""
import importlib
import json
import os
import sys
import types


def load_seal_code(code_root):
    pkg_dir = os.path.join(os.path.abspath(code_root), 'student_pilot')
    for name in ('source_seal.py', 'p3_provenance.py'):
        if not os.path.isfile(os.path.join(pkg_dir, name)):
            raise SystemExit('seal code missing: %s' % os.path.join(pkg_dir, name))
    sys.dont_write_bytecode = True
    for name in list(sys.modules):
        if name == 'student_pilot' or name.startswith('student_pilot.'):
            del sys.modules[name]
    pkg = types.ModuleType('student_pilot')
    pkg.__path__ = [pkg_dir]
    pkg.__package__ = 'student_pilot'
    sys.modules['student_pilot'] = pkg
    seal = importlib.import_module('student_pilot.source_seal')
    prov = importlib.import_module('student_pilot.p3_provenance')
    return seal.inventory, prov.digest


def main(argv):
    if len(argv) < 3 or argv[0] != '--code':
        raise SystemExit(__doc__)
    inventory, digest = load_seal_code(argv[1])
    out = {'code_root': os.path.abspath(argv[1]), 'trees': {}}
    ok = True
    for d in argv[2:]:
        try:
            files = inventory(d)
            out['trees'][d] = {'tree_sha256': digest(files), 'files': files}
        except (ValueError, OSError) as exc:
            out['trees'][d] = {'error': '%s: %s' % (type(exc).__name__, exc)}
            ok = False
    sys.stdout.write(json.dumps(out, sort_keys=True) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
