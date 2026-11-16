import json, subprocess, shutil
from pathlib import Path
AN=Path('/scratch/jjyeung/orch_n30/review_an2/run'); SRC=(AN/'out/native_vs_direct.py').read_text()
PY='/scratch/jjyeung/envs/p1cpu/bin/python3.12'
M={
 'R1_capped_direct_kept': ("return 0 if any(states.values()) else row['score'] if direct else native_score(row)",
                           "return row['score'] if direct else 0 if any(states.values()) else native_score(row)"),
 'R2_signature_sign_only': ("return ((d['points'] > 0) - (d['points'] < 0), lo > 0 or hi < 0)",
                            "return ((d['points'] > 0) - (d['points'] < 0),)"),
 'R3_signature_interval_only': ("return ((d['points'] > 0) - (d['points'] < 0), lo > 0 or hi < 0)",
                            "return (lo > 0 or hi < 0,)"),
 'R4_prod_err_direct_only': ("and not any(producer_error(arms[a][k]) for a in ARMS)]", "]"),
 'R5_metre_includes_cm': ("((TYPES[0], 'meters'), (TYPES[1], 'square meters'))", "((TYPES[0], 'meters'), (TYPES[0], 'centimeters'), (TYPES[1], 'square meters'))"),
 'R6_no_think_regex': ("no_final_answer |= not bool(re.search(r'</think\\s*>', decoded['text'] or '', re.I))", "pass"),
 'R7_direct_htc_not_nfa': ("no_final_answer |= bool(row.get('hit_token_cap') or row.get('stopped_unclosed'))", "no_final_answer |= bool(row.get('stopped_unclosed'))"),
 'R8_refusal_code_unchecked': ("require(ref.get('code') == REFUSAL_CODE, 'Geometry refusal code disagreement: ' + key)", "pass"),
}
env={'test_full_fixture_cli','test_real_pilot_cli'}; out={}
for name,(a,b) in M.items():
    n=SRC.count(a)
    if n!=1: out[name]=dict(error='occurrences %d'%n); print(name,out[name]); continue
    d=AN/'work/my_mutants'/name/'out'; (d/'tests').mkdir(parents=True,exist_ok=True)
    (d/'native_vs_direct.py').write_text(SRC.replace(a,b))
    for p in (AN/'out/tests').glob('*.py'): (d/'tests'/p.name).write_bytes(p.read_bytes())
    p=subprocess.run([PY,'-I','-s','-B',str(d/'tests/run_tests.py'),'--all'],capture_output=True,text=True,timeout=600)
    r=json.loads((d/'tests/RESULTS.json').read_text())
    k=sorted({f['test'].split()[0] for f in r['failures']+r['errors']}-env)
    out[name]=dict(killed=bool(k),tests=k); print(name,'KILLED' if k else 'SURVIVED',k[:3],flush=True)
(AN.parent/'work/MY_MUTANTS.json').write_text(json.dumps(out,indent=1))
