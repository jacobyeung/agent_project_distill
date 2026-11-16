from pathlib import Path
L=Path(__file__).resolve().parents[1];p=L/'work/real_audit_r5.py';s=p.read_text()
s=s.replace("report = dict(", '''import ast, inspect, re
from student_pilot import phrases
original = phrases.source_template_candidates
source = inspect.getsource(original)
variants = {}
replacements = {
 'vocabulary': ("            for category, labels in vocabulary().items():\\n                if normalize_phrase(category) in names:\\n                    names.update(phrase_set(labels))", "            pass"),
 'templates': ("for pattern in ANGLE_PATTERNS:", "for pattern in ():"),
 'aliases': ("names.update(aliases[n] for n in tuple(names) if n in aliases)", "pass")}
for name,(old,new) in replacements.items():
    assert source.count(old)==1
    namespace=dict(phrases.__dict__)
    exec(compile(source.replace(old,new),str(T/'student_pilot/phrases.py'),'exec'),namespace)
    variants[name]=namespace['source_template_candidates']
ablation={k:dict(admitted_only=0,examples=[]) for k in variants}
bare_gaps=dict(rows=0,events=0,examples=[],rule='ON only: base parse_response does not admit the bare scalar form')
report = dict(''',1)
s=s.replace("c['rows'] += 1", "c['rows'] += 1\n    examples=c.setdefault('examples',{'admitted':[],'deferred':[]})['deferred' if reason else 'admitted']\n    if len(examples)<3:examples.append(dict(qid=row.get('qid'),source=str(path),line=line))")
s=s.replace("                add(counts, typ, reason, row, path, line)", '''                if reason is None:
                    for name,fn in variants.items():
                        phrases.source_template_candidates=fn
                        refused=audit_training_contract([row])[0]
                        phrases.source_template_candidates=original
                        if refused:
                            ablation[name]['admitted_only']+=1
                            if len(ablation[name]['examples'])<3:
                                ablation[name]['examples'].append(dict(qid=row.get('qid'),source=str(path),line=line,reason=refused))
                bare=[(call,text) for call,text in call_responses(row) if isinstance(call,str) and call.startswith('<gap ') and isinstance(text,str) and re.fullmatch(r'\\s*(?:<tool_response>)?\\s*\\d+\\.\\d{2} m\\s*(?:</tool_response>)?\\s*',text)]
                if bare:
                    bare_gaps['rows']+=1;bare_gaps['events']+=len(bare)
                    if len(bare_gaps['examples'])<3:bare_gaps['examples'].append(dict(qid=row.get('qid'),source=str(path),line=line,revision=row.get('trace_revision',row.get('spec_version'))))
                add(counts, typ, reason, row, path, line)''')
s=s.replace("report['counting'] =", "report['ablations']=ablation\nreport['legacy_bare_gaps']=bare_gaps\nreport['counting'] =")
p.write_text(s)
