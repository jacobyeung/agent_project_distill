cd /project/community/jjyeung/okh7/n2r/ece5eea1c1ec94e169abf835
tar xzOf result.tar.gz STAGING.json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(list(d));[print(k,{kk:vv for kk,vv in v.items() if kk!="members"}) for k,v in d.items() if isinstance(v,dict) and k not in ("export_headers",)]' | cut -c1-300
cd /project/community/jjyeung/okh7/d9c35d0a
tar tvf a.tar
tar tvf d.tar | cut -c1-2 | sort | uniq -c
tar tvf b.tar | cut -c1 | sort | uniq -c
tar tvf b.tar | grep '^h' | head -3
