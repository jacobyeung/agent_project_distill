from pathlib import Path
L=Path(__file__).resolve().parents[1];p=L/'work/row_families_r6/compare.py';s=p.read_text()
s=s.replace("    if type(old) is not type(new) or old == {'missing': True} or new == {'missing': True}:return None\n",'')
a=s.index('    current_texts_valid = False\n');b=s.index('    if valid(b) and valid(n):\n        for path,old,new in diffs',a)
s=s[:a]+'''    current_texts_valid = False
    if valid(b) and valid(n):
        # First validate known audit payload and derived accounting changes.
        # Then require exact key sets, leaf types and scalar values in the
        # remaining row, allowing only heading substitutions in its strings.
        current_texts_valid = True
        def normalize(old, new, path=''):
            if type(old) is type(new) and isinstance(old, dict):
                extra = set(new) - set(old)
                for key in extra:
                    reason = mapping(family, variant, path+'/'+key, {'missing': True}, new[key])
                    if reason not in ('metric_only_boxes', 'mdg_bridge', 'normalized_phrases'):
                        return new
                if set(old) - set(new):return new
                return {key: normalize(old[key],new[key],path+'/'+key) for key in old}
            if type(old) is type(new) and isinstance(old, list) and len(old)==len(new):
                return [normalize(a,b,path+'/'+str(i)) for i,(a,b) in enumerate(zip(old,new))]
            if isinstance(old,str) and isinstance(new,str):return new
            reason = mapping(family, variant, path, old, new)
            return old if reason is not None else new
        checked = normalize(b['row'], n['row'])
        current_texts_valid = row_texts_valid(b['row'], checked)
'''+s[b:];p.write_text(s)
