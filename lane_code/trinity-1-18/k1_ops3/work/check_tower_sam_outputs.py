"""CPU check of a tower_sam root with the kit's own checked_phase (capture digest, sources, producer, file hashes)."""
import json, sys
KC = '/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a'
sys.path[:0] = [KC + '/work', KC + '/work/refit']
import k1_pipeline  # noqa: F401  (sets native paths, verifies sources)
import k1_phases as F, bindings as B
m = json.load(open(sys.argv[1])); root = sys.argv[2]
ok, bad, missing = 0, [], []
for c in m['captures']:
    try:
        F.checked_phase(c, root, 'tower_sam'); ok += 1
    except FileNotFoundError:
        missing.append(c['canonical'])
    except Exception as e:
        bad.append([c['canonical'], repr(e)[:200]])
print(json.dumps(dict(ok=ok, bad=bad, missing=len(missing), first_missing=missing[:5])))
