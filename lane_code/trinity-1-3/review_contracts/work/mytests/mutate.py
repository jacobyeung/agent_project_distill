"""Apply one mutation at a time to a copy of the patched tree and run the builder's suite."""
import json, shutil, subprocess, sys
from pathlib import Path
L = Path('/scratch/jjyeung/orch_n30/review_contracts/work')
import os
SRC = L / os.environ.get('MUT_SRC','trees/patched')
RUN = os.environ.get('MUT_RUN','runpt.sh')
TESTS = os.environ.get('MUT_TESTS','btests')
MUTS = [
 ('M1', 'student_pilot/geometry_profiles.py', "    if plane[0] >= UP_PLANE_MIN:\n", "    if plane[0] > UP_PLANE_MIN:\n"),
 ('M2', 'student_pilot/geometry_profiles.py', "np.median(margin[usable] / plane[usable]) <= 0", "np.median(margin[usable] / plane[usable]) < -0.05"),
 ('M3', 'trace_format/contracts.py', "np.linalg.norm(np.asarray(geometry.down)[:2]) >= UP_PLANE_MIN", "np.linalg.norm(np.asarray(geometry.down)[1:]) >= UP_PLANE_MIN"),
 ('M4', 'trace_format/contracts.py', "        if 'error:' in line.lower():\n            return 'error'\n", ""),
 ('M5', 'trace_format/contracts.py', "'size unavailable', 'unavailable')", "'size unavailable')"),
 ('M6', 'student_pilot/training_contract.py', "if retried or name is None or name == failed:", "if retried or name == failed:"),
 ('M7', 'student_pilot/training_contract.py', "if any(code in text for code in OPERATOR_FAULTS) or 'error:' in text.lower():", "if False:"),
 ('M8', 'student_pilot/live_instances314.py', "    if enabled and entry.get('depth_cut_applied', False):", "    if entry.get('depth_cut_applied', False):"),
 ('M9', 'student_pilot/phrases.py', "        if word.endswith('ies') and len(word) > 3:\n            word = word[:-3]+'y'\n        elif", "        if"),
 ('M10', 'student_pilot/carrier_c1_decode.py', "distance = np.linalg.norm(camera(call['j'])[1]-camera(call['i'])[1])", "distance = np.linalg.norm(camera(call['j'])[1]-camera(1)[1])"),
 ('M11', 'trace_format/box_v313.py', "        return np.asarray(geometry.cam(k)[1],float)", "        return np.asarray(geometry.cam(1)[1],float)"),
 ('M12', 'student_pilot/s1_routing.py', "        refusal = audit_training_contract([row], contract_manifest)[0]\n        if refusal:", "        refusal = audit_training_contract([row], contract_manifest)[0]\n        if False:"),
 ('M13', 'student_pilot/ground_v3.py', "names = getattr(source, 'cache', {}).get('phrases', getattr(source,'names',()))", "names = getattr(source,'names',())"),
 ('M14', 'trace_format/ground_v313.py', "        if not self.witness_points or not heading_available(self.geometry):", "        if not self.witness_points:"),

 ('M15', 'generator/derivgen_v7/derivgen/box_v313.py', "BoxRegistry = _epoch_dispatch(BoxRegistry, _runtime.BoxRegistry)\n", ""),
 ('M16', 'student_pilot/carrier_c1_routing.py', "if not recorded and not heading_available(geometry):", "if False:"),
 ('M17', 'student_pilot/s1_grounding.py', "batch.get(\"cache_phrases\", row.get(\"candidate_phrases\"))", "None"),
 ('M18', 'trace_format/ground_v313.py', "            for ordinal, obj in enumerate(entries if heading_available(self.geometry) else [], 1):", "            for ordinal, obj in enumerate(entries, 1):"),

 ('R1', 'student_pilot/carrier_c1_routing.py', "        if not heading_available(self, i):\n            delta", "        if not heading_available(self):\n            delta"),
 ('R2', 'student_pilot/carrier_c1_routing.py', "missing = [k for k in dict.fromkeys((i, j)) if not heading_available(self, k)]", "missing = []"),
 ('R3', 'trace_format/contracts.py', "\n                    or (status == 'heading unavailable' and status in line))", ")"),
 ('R4', 'student_pilot/training_contract.py', "if match and status != 'ok' and not partial_ground:", "if match and status != 'ok':"),
 ('R5', 'generator/derivgen_v7/derivgen/box_v313.py', "        if session.box_registry.states.get(name)!='ok':failure=(name,response_status(body));break\n    if not failure:\n        body=emit(f'<gap a=", "        if response_status(body)!='ok':failure=(name,response_status(body));break\n    if not failure:\n        body=emit(f'<gap a="),
 ('R6', 'student_pilot/carrier_c1_routing.py', "            return f\"f1 centre {vec(self.camera_pose(k)['camera_t_L1'])} m, yaw heading unavailable (frame {k})\"\n", "            pass\n"),
]
only = set(sys.argv[1:])
results = {}
for mid, rel, old, new in MUTS:
    if only and mid not in only: continue
    dst = L / 'trees/mut'
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(SRC, dst, symlinks=True)
    p = dst / rel; s = p.read_text()
    n = s.count(old)
    if n != 1:
        results[mid] = dict(file=rel, error=f'pattern count {n}'); print(mid, results[mid], flush=True); continue
    p.write_text(s.replace(old, new))
    r = subprocess.run([str(L / RUN), str(dst), str(L / TESTS), '-x'], capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    results[mid] = dict(file=rel, old=old.strip()[:120], new=new.strip()[:120], suite_rc=r.returncode,
                        killed=r.returncode != 0, tail=tail)
    print(mid, 'KILLED' if r.returncode else 'SURVIVED', tail[-1] if tail else '', flush=True)
json.dump(results, open(L / (os.environ.get('MUT_TAG','')+'MUTATION_RESULTS%s.json' % ('_' + '_'.join(sorted(only)) if only else '')), 'w'), indent=1)
