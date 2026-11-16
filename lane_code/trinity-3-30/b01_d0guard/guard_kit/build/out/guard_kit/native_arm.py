"""Select one arm at the existing authenticated worker AST boundary."""
import ast
from copy import deepcopy

def select_native(pair_node):
    result = deepcopy(pair_node)
    matches = [n for n in ast.walk(result) if isinstance(n, ast.FunctionDef) and n.name == 'serve_pair']
    if len(matches) != 1:
        raise ValueError('Unrecognized item-serving boundary')
    serve = matches[0]
    starts = [i for i,n in enumerate(serve.body) if isinstance(n, ast.Assign)
              and [ast.unparse(t) for t in n.targets] == ['script']]
    if len(starts) != 1 or starts[0] < 1:
        raise ValueError('Unrecognized scripted-arm boundary')
    index = starts[0]
    expected = ["script = refusal_decode(refusal, scripted=True) if refusal else P.scripted(task, refs, geo, backend)",
                "if not P.replay(script, geo, backend)['byte_equal']:\n    raise ValueError('Scripted runtime replay differs')",
                "pair.append(make_record(task, script, request, prefill, 'scripted'))", 'return pair']
    if [ast.unparse(n) for n in serve.body[index:]] != expected:
        raise ValueError('Scripted-arm source structure differs')
    # The complete native serving prefix remains structurally identical.
    serve.body = serve.body[:index]+[ast.Return(value=ast.Name(id='pair',ctx=ast.Load()))]
    result.name = 'native_item'
    return ast.fix_missing_locations(result)

class NativeRefusals:
    def __init__(self, original):self.original = original
    def __getattr__(self, name):return getattr(self.original, name)
    def paired_item(self, task, request, unit, serve):
        if task['id'] in request['geometry_refusals']:
            return [self.original.refusal_pair(task,request,unit)[0]]
        rows = serve()
        if len(rows) != 1 or rows[0]['arm'] != 'unflagged':
            raise ValueError('Native arm cardinality differs')
        return rows

def compile_native(parts, namespace, kernels):
    return kernels.function(select_native(parts['pair']), {**namespace, 'GR':NativeRefusals(namespace['GR'])})
