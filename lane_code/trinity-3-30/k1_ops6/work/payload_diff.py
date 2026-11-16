import base64, hashlib, io, json, re, sys, tarfile
def payload(sh):
    t = open(sh).read()
    b64 = re.search(r"b64decode\('([A-Za-z0-9+/=]+)',validate=True\)", t).group(1)
    sha = re.search(r"hexdigest\(\)!='([0-9a-f]{64})'", t).group(1)
    raw = base64.b64decode(b64)
    assert hashlib.sha256(raw).hexdigest() == sha
    tf = tarfile.open(fileobj=io.BytesIO(raw))
    files = {m.name: tf.extractfile(m).read() for m in tf.getmembers()}
    return files, t.replace(b64, 'B64').replace(sha, 'SHA'), sha
old, ot, osha = payload(sys.argv[1]); new, nt, nsha = payload(sys.argv[2])
res = dict(old_payload_sha=osha, new_payload_sha=nsha, members_old=len(old), members_new=len(new),
           added=sorted(set(new) - set(old)), removed=sorted(set(old) - set(new)),
           changed=sorted(k for k in old if k in new and old[k] != new[k]),
           launcher_text_equal_except_payload_and_sha=ot == nt,
           a_json_equal=old.get('a.json') == new.get('a.json'))
print(json.dumps(res, indent=1))
