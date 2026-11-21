"""fix17 static check: in the decoded inner shell of the new kit (and of 929ab213 for contrast), the five sandboxed
python steps a, d, h, rv, t take only $Q_NS paths, and $Q_NJ appears only in its definition, the /data2 map target
Q_E4 and the sandbox bind; in b/*.py only pf.audit_roots/frames and a.restoring_admit name the second spelling;
the tree's production_proof reaches admit through the module attribute a.py replaces. Usage: st34.py <new kit> <old kit>."""
import sys, json, base64, re, tarfile, io
from pathlib import Path
NEW, OLD = Path(sys.argv[1]), Path(sys.argv[2])
def sh(k): return base64.b64decode(json.loads((k/'k/j.json').read_text())['payload']).decode()
def scan(text):
    steps, nj = {}, []
    for i, line in enumerate(text.splitlines(), 1):
        m = re.search(r'\$Q_KIT/b/(a|d|h|rv|t)\.py"\s+(.*?)\s+2>&1', line)
        if m:
            args = m.group(2)
            steps[m.group(1)] = dict(line=i, args=args, ns_only=('$Q_NS' in args and '$Q_NJ' not in args and 'Q_NJ' not in args))
        if 'Q_NJ' in line and not line.lstrip().startswith('#'): nj.append((i, line.strip()))
    return steps, nj
out = {}
for tag, k in (('new', NEW), ('old_929ab213', OLD)):
    steps, nj = scan(sh(k)); out[tag] = dict(steps=steps, q_nj_lines=nj)
s, nj = out['new']['steps'], out['new']['q_nj_lines']
def kind(l):
    if re.match(r'Q_NJ="/tmp/jjyeung/\$\{Q_NS#/tmp/\}"$', l): return 'definition'
    if l.startswith('export Q_E4=') and '$Q_NJ/p/q/f/' in l: return 'map_target_Q_E4'
    if '--bind "$Q_ROOT" "$Q_NJ"' in l: return 'sandbox_bind'
    return 'OTHER'
out['new_q_nj_kinds'] = [kind(l) for _, l in nj]
out['check_five_steps_present'] = sorted(s) == ['a', 'd', 'h', 'rv', 't']
out['check_five_steps_ns_only'] = all(v['ns_only'] for v in s.values())
out['check_q_nj_only_definition_map_bind'] = all(k != 'OTHER' for k in out['new_q_nj_kinds']) and {'definition', 'map_target_Q_E4', 'sandbox_bind'} <= set(out['new_q_nj_kinds'])
py = {}
for p in sorted((NEW/'b').glob('*.py')):
    hits = [(i, l.strip()) for i, l in enumerate(p.read_text().splitlines(), 1) if ('jjyeung' in l or 'audit_roots' in l)]
    if hits: py[p.name] = hits
out['b_py_second_name_or_audit_roots'] = py
out['check_b_py_only_pf_and_a'] = set(py) <= {'pf.py', 'a.py'}
out['other_sh_q_nj_or_jjyeung'] = {str(p.relative_to(NEW)): [i for i, l in enumerate(p.read_text().splitlines(), 1) if 'Q_NJ' in l or 'jjyeung' in l] for p in sorted(NEW.rglob('*.sh'))}
out['check_other_sh_clean'] = not any(out['other_sh_q_nj_or_jjyeung'].values())
tar = next((NEW/'k').glob('t_*.tar'))
with tarfile.open(tar) as t:
    pp = t.extractfile('launch_r1/production_proof.py').read().decode()
out['production_proof_admit_refs'] = [(i, l.strip()) for i, l in enumerate(pp.splitlines(), 1) if re.search(r'\badmit\b', l) and ('import' in l or 'admit(' in l)]
out['all_ok'] = out['check_five_steps_present'] and out['check_five_steps_ns_only'] and out['check_q_nj_only_definition_map_bind'] and out['check_b_py_only_pf_and_a'] and out['check_other_sh_clean']
print(json.dumps(out, indent=1))
