"""n_ops10 patch 2 of nauto.py (ORCH ORDER 0912Z items 4-5): extra /project BLOCKERs at 10, 8 (before the gate passes) and 5 GiB. Usage: python3 patch_nauto2.py SRC DST"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
def rep(old, new):
    global s
    assert s.count(old) == 1, ('not unique', old[:80])
    s = s.replace(old, new)
rep("if free is not None and free < 22: fl.append('PROJECT_FS<22G %d GiB free' % free)",
    "if free is not None and free < 22: fl.append('PROJECT_FS<22G %d GiB free' % free)\n"
    "if free is not None and free < 10: fl.append('PROJECT_FS<10G %d GiB free' % free)\n"
    "if free is not None and free < 8 and not re.search(r'\"step\":\\s*\\d', line): fl.append('PROJECT_FS<8G_BEFORE_GATE %d GiB free' % free)\n"
    "if free is not None and free < 5: fl.append('PROJECT_FS<5G %d GiB free' % free)")
rep("'NAMEWORD', 'NAMEFORM', 'ADV_OTHERS')",
    "'NAMEWORD', 'NAMEFORM', 'ADV_OTHERS', 'PROJECT_FS<10G', 'PROJECT_FS<8G_BEFORE_GATE', 'PROJECT_FS<5G')")
rep(" 'ADV_OTHERS': (",
    " 'PROJECT_FS<10G': ('grep @@DF MON/last.raw; tail B/events/n_ops/PROJECT_FS_FREE.txt', 'ORDER 0912Z: ask the user to free space from B/events/n_ops/ORCHARD_REMOVAL_CANDIDATES_20261121.md (no agent removes anything on /project)'),\n"
    " 'PROJECT_FS<8G_BEFORE_GATE': ('grep @@DF MON/last.raw; cat X/o/<job>_live/gate.txt', 'ORDER 0912Z item 5: the gate files, fallback copy and review install need space; ask the user now with the top entries of ORCHARD_REMOVAL_CANDIDATES_20261121.md'),\n"
    " 'PROJECT_FS<5G': ('grep @@DF MON/last.raw', 'ORDER 0912Z: as PROJECT_FS<10G, now urgent'),\n"
    " 'ADV_OTHERS': (")
open(dst, 'x').write(s)
print('patched', dst)
