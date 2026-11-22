"""Run the tree's own plan() (extracted by source, without importing torch) and the check() byte arithmetic."""
import ast, json, sys
SRC = sys.argv[1]
tree = ast.parse(open(SRC).read())
ns = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'plan':
        try:
            module = ast.Module([node], [])
        except TypeError:
            module = ast.Module([node])
        exec(compile(module, SRC, 'exec'), ns)
plan = ns['plan']
MIB64 = 64 * 1024 ** 2

def state_bytes(measured): return (measured * 5 + 3) // 4 + MIB64
def export_bytes(exported): return (exported * 10 + 3) // 4 + MIB64

def required(policy, S, E, done_states=0, done_exports=0):
    states = policy['planned_full_states'] + policy['extra_full_states'] - done_states
    exports = policy['planned_weight_exports'] - done_exports
    native = states * S + exports * E
    archive = policy.get('retained_archive_copies', 0) * (states * (S + 10240) + exports * (E + 10240))
    return dict(states=states, exports=exports, native=native, archive=archive,
                required=native + archive + policy['reserve_bytes'])

if __name__ == '__main__':
    args = json.loads(sys.argv[2])
    M, X = args['M'], args['X']
    S, E = state_bytes(M), export_bytes(X)
    print(json.dumps(dict(M=M, X=X, S=S, E=E)))
    for label, recipe, copies in args['cases']:
        p = plan(recipe, retained_archive_copies=copies)
        r = required(p, S, E)
        print(label, json.dumps(p), json.dumps(r), 'TB', round(r['required'] / 1e12, 4), 'GiB', round(r['required'] / 2 ** 30, 1))
