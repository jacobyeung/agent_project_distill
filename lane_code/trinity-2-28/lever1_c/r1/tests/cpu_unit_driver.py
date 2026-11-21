"""Run the delivered operator's CPU real unit (cpu_unit) as the CPU check does.

argv: <package> <operator a/6.py> <config.json> <out.json>. The operator
launches the production worker through its prefix seam; the receipts it and
the worker write are copied to <out.json>.
"""
import json
from pathlib import Path
import runpy
import sys

package, operator, config_path, out = sys.argv[1:5]
p = Path(package)
sys.path[:0] = [str(p/'b'), str(p/'tree'), str(p)]
import l
l.install(p)
from orchard_h10.common import install_process_guard
install_process_guard(Path(config_path).resolve().parent)
config = json.loads(Path(config_path).read_text())
op = runpy.run_path(operator, run_name='cpu_unit_driver')
process = op['cpu_unit'](config)
meta = Path(config['output'])/'metadata'
unit = json.loads(l.install(p).Path(meta/'33.json').read_text()) if (meta/'33.json').exists() else None
Path(out).write_text(json.dumps(dict(process=process, unit=unit), indent=2, default=str)+'\n')
