# Adapts the jn5 harness (build 24m4z13b) to compare jn5 with jn6. Usage: python3 adapt.py <J>
import sys,re
from pathlib import Path
J=Path(sys.argv[1]);src=J/'work/build24m4z13b';dst=J/'work/build26';dst.mkdir()
s=(src/'test_jn5.py').read_text()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(a,s.count(a));s=s.replace(a,b)
rep("W=J/'work/build24m4z13b'","W=J/'work/build26'")
rep("    if version=='5':\n","    if version in ('5','6'):\n")
rep("        timeouts=[e['args'] for e in events if e['event']=='timeout']\n",
    "        timeouts=[e['args'] for e in events if e['event']=='timeout']\n"
    "        # jn6: the live mirror's own bounded calls are not publication attempts.\n"
    "        mirror=[a for a in timeouts if any(str(v).endswith('j6.py') for v in a)]\n"
    "        timeouts=[a for a in timeouts if a not in mirror]\n"
    "        if version=='6' and not setup:\n"
    "            live=x/'o'/(job+'_live')/'live.json'\n"
    "            assert live.is_file() and json.loads(live.read_text())['phase']=='final',(label,'no final live snapshot')\n"
    "            assert any(a[:2]==['--signal=KILL','30s'] for a in mirror),(label,'final snapshot not bounded',mirror)\n"
    "            assert sum(f.stat().st_size for f in live.parent.iterdir())<2_000_000\n")
rep("    if pfail=='hang' and version=='5': assert 119<elapsed<124,elapsed","    if pfail=='hang' and version=='5': assert 119<elapsed<124,elapsed\n    # jn6 adds at most the 30 s final snapshot after the 120 s publish and 15 s fallback.\n    if pfail=='hang' and version=='6': assert 119<elapsed<124+31,elapsed")
rep("            try: rc=p.wait(timeout=124 if pfail=='hang' else 20)","            try: rc=p.wait(timeout=(124 if version=='5' else 160) if pfail=='hang' else 20)")
rep("for v in ('4','5')","for v in ('5','6')",3)
(dst/'test_jn6.py').write_text(s)
e=(src/'test_extra.py').read_text().replace("with_name('test_jn5.py')","with_name('test_jn6.py')").replace("for v in ('4','5')","for v in ('5','6')")
(dst/'test_extra6.py').write_text(e);print('adapted')
