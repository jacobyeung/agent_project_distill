"""Apply one mutation per fresh copy of the r4 base-applied tree and run the builder's r4 suite (-x). Never removes anything."""
import json, shutil, subprocess, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
L = Path('/scratch/jjyeung/orch_n30/review_contracts2/work')
SRC = L/'rr/work/trees/r4_applied'; TESTS = L/'rr/work/tests_r4'
G = 'generator/derivgen_v7/derivgen/'
MUTS = [
 # first reviewer's 18, adapted to r4 code
 ('M1','student_pilot/geometry_profiles.py',"    if plane[0] >= UP_PLANE_MIN:\n","    if plane[0] > UP_PLANE_MIN:\n"),
 ('M2','student_pilot/geometry_profiles.py',"np.median(margin[usable] / plane[usable]) <= 0","np.median(margin[usable] / plane[usable]) < -0.05"),
 ('M3','trace_format/contracts.py',"(np.asarray(rotation).T @ down)[:2]","(np.asarray(rotation).T @ down)[1:]"),
 ('M4','trace_format/contracts.py',"    if body.lower().startswith('error:'):\n        return 'error'\n",""),
 ('M5','trace_format/contracts.py',"'size unavailable', 'unavailable')","'size unavailable')"),
 ('M6','student_pilot/training_contract.py',"if retried or name is None or name == failed:","if retried or name == failed:"),
 ('M7','student_pilot/training_contract.py',"if any(code in text for code in OPERATOR_FAULTS + RUNTIME_ONLY_FAULTS):","if False:"),
 ('M8','student_pilot/live_instances314.py',"    if enabled and entry.get('depth_cut_applied', False):","    if entry.get('depth_cut_applied', False):"),
 ('M9','student_pilot/phrases.py',"        if word.endswith('ies') and len(word) > 3:\n            word = word[:-3]+'y'\n        elif","        if"),
 ('M10','student_pilot/carrier_c1_routing.py',"delta = self.camera(j)[1] - self.camera(i)[1]","delta = self.camera(j)[1] - self.camera(1)[1]"),
 ('M11','trace_format/box_v313.py',"        return np.asarray(geometry.cam(k)[1],float)","        return np.asarray(geometry.cam(1)[1],float)"),
 ('M12','student_pilot/s1_routing.py',"        refusal = audit_training_contract([row], contract_manifest)[0]\n        if refusal:","        refusal = audit_training_contract([row], contract_manifest)[0]\n        if False:"),
 ('M13','student_pilot/ground_v3.py',"names = getattr(source, 'cache', {}).get('phrases', getattr(source,'names',()))","names = getattr(source,'names',())"),
 ('M14','trace_format/ground_v313.py',"heading_defined=heading_available(geometry))","heading_defined=heading_available(geometry) or role == 'nearest point')"),
 ('M15',G+'box_v313.py',"BoxRegistry = epoch_class(BoxRegistry, _runtime.BoxRegistry)\n",""),
 ('M16','student_pilot/carrier_c1_routing.py',"if not recorded and (not heading_available(geometry) or","if False and (not heading_available(geometry) or"),
 ('M17','student_pilot/s1_grounding.py',"batch.get(\"cache_phrases\", row.get(\"candidate_phrases\"))","None"),
 ('M18','trace_format/ground_v313.py',"heading_defined=heading_available(geometry))","heading_defined=heading_available(geometry) or role.startswith('instance '))"),
 # first reviewer's r2 mutants (R3 has no r4 counterpart: response_status reads only the first line)
 ('R1','student_pilot/carrier_c1_routing.py',"        if not heading_available(self, i):\n            delta","        if not heading_available(self):\n            delta"),
 ('R2','student_pilot/carrier_c1_routing.py',"missing = [k for k in dict.fromkeys((i, j)) if not heading_available(self, k)]","missing = []"),
 ('R4','student_pilot/training_contract.py',"if call.startswith('<ground') and status != 'ok' and not partial_ground:","if call.startswith('<ground') and status != 'ok':"),
 ('R5',G+'box_v313.py',"        if session.box_registry.states.get(name)!='ok':failure=(name,response_status(body));break\n    if not failure:\n        body=emit(f'<gap a=","        if response_status(body)!='ok':failure=(name,response_status(body));break\n    if not failure:\n        body=emit(f'<gap a="),
 ('R6','student_pilot/carrier_c1_routing.py',"        if not heading_available(self, k):\n","        if False:\n"),
 # my mutants, all in code r3 or r4 introduced
 ('N1','trace_format/point_events.py',"f\"dx = {delta[0]:+.2f} m, dy","f\"dx = {delta[0]:.2f} m, dy"),
 ('N2','student_pilot/training_contract.py',"if ('call_id' in call or 'call_id' in event) and call.get('call_id') != event.get('call_id'):","if False:"),
 ('N3','student_pilot/live_trace313.py',"if program_version in ('3.12', '3.12.1', '3.12.2') and re.fullmatch(","if program_version in ('3.12',) and re.fullmatch("),
 ('N4','student_pilot/phrases.py',"            for category, labels in vocabulary().items():\n                if normalize_phrase(category) in names:\n                    names.update(phrase_set(labels))\n","            pass\n"),
 ('N5','student_pilot/carrier_c1_routing.py',"return 'f1 centre '+partial_f1(self.camera_pose(k)['camera_t_L1'], f2)+f' m, yaw heading unavailable (frame {k})'","return 'f1 centre '+vec(self.camera_pose(k)['camera_t_L1'])+f' m, yaw heading unavailable (frame {k})'"),
 ('N6','trace_format/contracts.py',"    if body == 'heading unavailable' and any(\n            line.startswith(('size ', 'distance ', 'count ')) and 'unavailable' not in line\n            for line in text.splitlines()[1:]):\n        return 'ok'\n",""),
 ('N7','student_pilot/training_contract.py',"r': (?:frames |[1-9][0-9]* (?:instances|found)\\n)'","r': (?:frames )'"),
 ('N8','trace_format/contracts.py',"key = (cls, new_contracts())","key = (cls, True)"),
 ('N9','trace_format/box_v313.py',"    if geometry_mode == 'sensor':\n        return FusedBoxProvider()\n","    if geometry_mode == 'sensor' and __import__('trace_format.contracts', fromlist=['x']).new_contracts():\n        return FusedBoxProvider()\n"),
 ('N10','student_pilot/phrases.py',"not word.endswith(('ss','us','is','ses','ves'))","not word.endswith(('ss','us','is'))"),
 ('N11','student_pilot/s1_grounding.py',"batch.get(\"cache_phrases\", row.get(\"candidate_phrases\"))","batch.get(\"cache_phrases\", row.get(\"candidate_manifest\", row.get(\"cache_phrases\", row.get(\"candidate_phrases\"))))"),
]
only = set(sys.argv[1:])
def run(m):
    mid, rel, old, new = m
    dst = L/'mut'/mid
    k = 1
    while dst.exists():
        k += 1; dst = L/'mut'/f'{mid}_{k}'
    shutil.copytree(SRC, dst, symlinks=True)
    p = dst/rel; s = p.read_text(); n = s.count(old)
    if n != 1: return mid, dict(file=rel, error=f'pattern count {n}')
    p.write_text(s.replace(old, new))
    r = subprocess.run([str(L/'runpt.sh'), str(dst), str(TESTS), 'mut_'+dst.name, str(TESTS), '-x'], capture_output=True, text=True)
    tail = (r.stdout+r.stderr).strip().splitlines()
    failed = [l for l in tail if l.startswith(('FAILED', 'ERROR'))]
    return mid, dict(file=rel, old=old.strip()[:160], new=new.strip()[:160], suite_rc=r.returncode, killed=r.returncode != 0,
                     first_failure=failed[:2], tail=tail[-1:])
todo = [m for m in MUTS if not only or m[0] in only]
res = {}
with ThreadPoolExecutor(8) as ex:
    for mid, r in ex.map(run, todo):
        res[mid] = r
        print(mid, 'ERROR '+r['error'] if 'error' in r else ('KILLED' if r['killed'] else 'SURVIVED'), r.get('first_failure', ''), flush=True)
json.dump(res, open(L/('MUTATIONS_R4_REVIEW%s.json' % ('_'+'_'.join(sorted(only)) if only else '')), 'w'), indent=1)
