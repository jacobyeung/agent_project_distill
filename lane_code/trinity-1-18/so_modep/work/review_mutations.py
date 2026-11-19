"""Deliberately broken implementations, installed only by the regression runner."""
from pathlib import Path
import ast


CASES = {
    'sql_reverse_chunks': ('s1_exclusions', '_selected_rows',
        'for start in range(0, len(ordered), 256):',
        'for start in reversed(range(0, len(ordered), 256)):'),
    'sql_reverse_rows': ('s1_exclusions', '_selected_rows',
        "') ORDER BY i', batch)", "') ORDER BY i DESC', batch)"),
    'sql_ignore_on': ('s1_exclusions', '_database',
        "os.environ.get('S1_PREP_SELECT_SQL') == '1'", 'False'),
    'paths_ignore_on': ('orchard_paths', 'resolve_read',
        "if os.environ.get('S1_PREP_FAST_PATHS') == '1':", 'if False:'),
    'parser_literal': ('orchard_paths', '_mapping_items',
        'mapping.__getattribute__("sp" "lit")(\'=\', 1)', "mapping.split('=', 1)"),
}


def install(name):
    import importlib
    module_name, function, old, new = CASES[name]
    module = importlib.import_module('student_pilot.'+module_name)
    text = Path(module.__file__).read_text()
    assert old in text, (name, old)
    text = text.replace(old, new)
    root = Path(__file__).resolve().parent/'review1_mutations'
    root.mkdir(exist_ok=True)
    source = root/(name+'.py')
    source.write_text(text)
    node = next(node for node in ast.parse(text).body
                if isinstance(node, ast.FunctionDef) and node.name == function)
    # Preserve the real module globals so test spies and PROJECT patches still apply.
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), module.__dict__)
    print('DELIBERATE_MUTATION '+name+' '+str(source), flush=True)
