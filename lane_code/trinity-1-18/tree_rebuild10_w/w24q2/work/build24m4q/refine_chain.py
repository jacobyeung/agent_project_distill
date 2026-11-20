from pathlib import Path
import time
L=Path.cwd()
def edit(name,fn):
 p=L/name;s=fn(p.read_text());a=L/'attic/build24m4q'/name;a.parent.mkdir(parents=True,exist_ok=True)
 if a.exists():a=a.with_name(a.name+'.'+str(time.time_ns()))
 p.rename(a);p.write_text(s)
def ch(s):
 s=s.replace("TREE = 'de202", "DB = '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'\nTREE = 'de202")
 s=s.replace("        summary['source_fields']", "        summary['source_sha256'] = sha256(pinned(pin))\n        summary['source_qid_set_sha256'] = key_hash(list(source['rows']))\n        summary['source_fields']")
 s=s.replace("        old_digests = {}; duplicates = set()", "        n_equal = sum(source['rows'].get(q, {}).get('content_sha256') == h for q,h in rows.items())\n        summary.update(pinned_N_content_equal=n_equal, pinned_N_content_mismatch=len(rows)-n_equal)\n        summary['P_database_sha256'] = sha256(directory/'base/rows.sqlite')\n        if summary['P_database_sha256'] != DB:\n            raise ValueError('E98:gate')\n        control = directory/'base_input.json'\n        if control.is_file():\n            p_config = load(control)['config']\n            summary['P_config_sha256'] = digest(p_config)\n            summary['P_config_extent_receipt'] = p_config.get('extent_receipt')\n        old_digests = {}; duplicates = set(); p_pool = set()")
 s=s.replace("                if qid in rows:\n                    if qid in old_digests:","                if value.get('s1_source'):\n                    p_pool.add(qid)\n                if qid in rows or qid in source['rows']:\n                    if qid in old_digests:")
 s=s.replace("        absent = sorted(set(rows)-set(source['rows']))", "        common = set(old_digests) & set(source['rows'])\n        summary.update(P_pool_rows=len(p_pool), P_pool_qid_set_sha256=key_hash(list(p_pool)),\n            source_qids_in_P=len(common), source_qids_absent_from_P=len(set(source['rows'])-common),\n            source_content_equal_P=sum(source['rows'][q].get('content_sha256') == old_digests[q] for q in common))\n        absent = sorted(set(rows)-set(source['rows']))")
 s=s.replace("        value['streams'][stream] = result\n", "        value['streams'][stream] = result\n        if stream == 'routing':\n            value['population'].update(database_rows=result.get('database_rows'),\n                database_key_set_sha256=result.get('database_key_set_sha256'))\n")
 return s
edit('out/rcj/ch.py',ch)
def x(s):
 a=s.index("        timing['task_a']['task_iv'] = chain['status']");b=s.index("    if mode=='r' and all(p.is_file() for p in bases):",a)
 s=s[:a]+'''        timing['task_a']['task_iv'] = chain['status']
        population_status = (chain.get('population') or {}).get('status', 'UNAVAILABLE')
        timing['task_a']['population_status'] = population_status
        timing['task_a']['task_i_content'] = timing['task_a'].get('task_i', 'UNAVAILABLE')
        if timing['task_a'].get('task_i') == 'PASS':
            if chain['status'] != 'PASS':
                timing['task_a']['task_i'] = 'FAIL'
            elif population_status != 'PASS':
                timing['task_a']['task_i'] = 'UNAVAILABLE'
        if chain['status'] != 'PASS':
            timing['task_a']['status'] = 'FAIL'
        elif timing['task_a'].get('status') == 'PASS' and timing['task_a'].get('task_i') != 'PASS':
            timing['task_a']['status'] = 'UNAVAILABLE'
'''+s[b:]
 return s
edit('out/rcj/x.py',x)
# Fixture databases may satisfy the production gate only within this test patch.
p=L/'work/build24m4q/tests.py';s=p.read_text().replace("v=ch.candidate(c,root,root);", "\n  with patch.object(ch,'DB',file_pin(root/'base/rows.sqlite')['sha256']):v=ch.candidate(c,root,root)\n  ",1)
# Fix the second occurrence at the loop's indentation.
s=s.replace("   v=ch.candidate(c,root,root);self.assertEqual", "   with patch.object(ch,'DB',file_pin(root/'base/rows.sqlite')['sha256']):v=ch.candidate(c,root,root)\n   self.assertEqual")
edit('work/build24m4q/tests.py',lambda _:s)
p=L/'work/build24m4q/publication_tests.py';s=p.read_text()
s=s.replace("bt['task_a'].pop('task_iv');bt['task_a'].pop('population_status')", "bt['task_a'].pop('task_iv');bt['task_a'].pop('population_status')\n            bt['task_a']['task_i'] = bt['task_a'].pop('task_i_content')\n            if bt['task_a']['status'] == 'UNAVAILABLE':bt['task_a']['status'] = 'PASS'")
s=s.replace("task_iv='PASS',population_status='NOT_REACHED'", "task_iv='PASS',population_status='NOT_REACHED',task_i_content='FAIL'")
edit('work/build24m4q/publication_tests.py',lambda _:s)
