from pathlib import Path
import ast,hashlib,json,re,sys
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/build12'
sys.path.insert(0,str(T))
from student_pilot.r2_adapters import normalize
from student_pilot import row_text_audit as audit
source=L/'work/n1fix2/proof_text.py'
node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='norm')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'))
results={}
for family in ('a0_recovery','a0_units','a0_pool_abs_distance_reworded','a0_room'):
    path=L/'work/rows_slices/slices_final'/(family+'.jsonl');count=0;changes=[]
    for line in path.open():
        count+=1;assert count<=2000
        row=norm(json.loads(line))
        authored='\n'.join(re.sub(r'<tool_response>[^<>]*</tool_response>','',str(row.get(k,'')))
            if audit.recorded_responses(row,str(row.get(k,''))) else str(row.get(k,''))
            for k in ('target','suffix','response','trace'))
        thoughts='\n'.join(re.findall(r'<think>(.*?)</think>',authored,re.S))
        if not thoughts.isascii() and not audit.reasons(row):
            changes.append(dict(qid=row.get('qid'),codepoints=sorted({f'U+{ord(c):04X}' for c in thoughts if ord(c)>127})))
    results[family]=dict(rows=count,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),changed_rows=changes)
out=B/'proofs/text_policy';out.mkdir(parents=True,exist_ok=True)
changed=any(r['changed_rows'] for r in results.values())
(out/'ASCII_CANDIDATE.json').write_text(json.dumps(dict(families=results,adopt=not changed),indent=2))
p=T/'student_pilot/row_text_audit.py';s=p.read_text()
if changed:
    s=s.replace("0x39f:'O',0x43e:'o',0x41e:'O',0x2800:None,", "0x39f:'O',0x43e:'o',0x41e:'O',0x2800:None,\n        0x455:'s',0x422:'T',0x430:'a',0x456:'i',0x441:'c',0x39d:'N',0x3a4:'T',0x585:'o',")
    s=s.replace("'еЕοΟоОᴀ", "'ѕТаісΝΤօеЕοΟоОᴀ").replace("'eEoOoOabcdefgh", "'sTaicNToeEoOoOabcdefgh")
else:
    s=s.replace("    found=[key for key,pattern in PATTERNS.items()", "    non_ascii = any(not t.isascii() for t in re.findall(r'<think>(.*?)</think>', authored, re.S))\n    found=['non_ascii_authored_think'] if non_ascii else []\n    found += [key for key,pattern in PATTERNS.items()")
    s=s.replace("    found=[]\n    for name,pattern,content", "    raw_authored = '\\n'.join(re.sub(r'<tool_response>[^<>]*</tool_response>', '', s)\n        if recorded_responses(row,s) else s for s in fields)\n    found = ['non_ascii_authored_think'] if any(not t.isascii() for t in\n        re.findall(r'<think>(.*?)</think>',raw_authored,re.S)) else []\n    for name,pattern,content")
p.write_text(s)
with (B/'DECISIONS.md').open('a') as f:
    f.write('\nText-policy result: '+('ASCII-only changes original slice verdicts; retain per-character maps expanded to the eight reviewed glyphs. The confusable class remains open.' if changed else 'ASCII-only authored think text preserves all original slice verdicts and closes non-ASCII confusables.')+' Evidence: proofs/text_policy/ASCII_CANDIDATE.json.\n')
print(json.dumps(dict(adopt_ascii=not changed,changes={k:len(v['changed_rows']) for k,v in results.items()})))
