F=/project/community/jjyeung/cp4tk_fr/k6tk
zcat $F/MEMBERS.tsv.gz | grep -E '^(836d07a5f0c8bac4d5351b57d8e03600bb63f6754611d8454c2a140c36ba6196|8a8ff814d7c871cb2eb4a4af7e4254a9ce5004504a42efe4926f8612d96da843)' | python3 -c '
import base64, hashlib, os, sys
F = "/project/community/jjyeung/cp4tk_fr/k6tk/parts"
for line in sys.stdin:
    sha, shard = line.split()
    path = os.path.join(F, shard.split("_")[0], shard); name = sha[:2] + "/" + sha + ".png"
    found = None
    with open(path, "rb") as f:
        off = 0
        while True:
            f.seek(off); h = f.read(512)
            if len(h) < 512 or h == bytes(512): break
            mname = h[0:100].split(b"\0")[0].decode(); prefix = h[345:500].split(b"\0")[0].decode()
            size = int(h[124:136].split(b"\0")[0].strip() or b"0", 8)
            if ((prefix + "/" + mname) if prefix else mname) == name:
                f.seek(off + 512); found = f.read(size); break
            off += 512 + (size + 511) // 512 * 512
    print("FILE", sha, shard, len(found) if found else None, hashlib.sha256(found).hexdigest() if found else None)
    if found: print(base64.b64encode(found).decode())
'
