"""The reader's routed_features.resize, loaded without model dependencies."""
import ast
from pathlib import Path
import numpy as np
from scipy import ndimage
from gpkg.source_pins import checked

SOURCE = Path(__file__).resolve().parents[1]/'work/payload/tree/student_pilot/routed_features.py'
_tree = ast.parse(checked(SOURCE))
_fn = next(n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name == 'resize')
_ns = dict(np=np, ndimage=ndimage)
exec(compile(ast.Module(body=[_fn], type_ignores=[]), str(SOURCE), 'exec'), _ns)
resize = _ns['resize']
