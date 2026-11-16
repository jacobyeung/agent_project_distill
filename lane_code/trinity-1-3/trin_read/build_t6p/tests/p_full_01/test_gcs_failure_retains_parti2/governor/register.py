import json,os,signal,sys
from pathlib import Path
a=sys.argv[1:];get=lambda k:a[a.index(k)+1]
pid=int(get("--pid"))
assert Path("/proc/%d/stat"%pid).read_text().split()[2]=="T"
assert Path("/proc/%d/comm"%pid).read_text().strip()=="bash"
assert get("--member-pid")==get("--rl-pid")
assert get("--expected-bytes")=="20" and get("--priority")=="37"
Path('/scratch/jjyeung/orch_n30/trin_read/build_t6p/tests/p_full_01/test_gcs_failure_retains_parti2/streams/fixture.json').write_text(json.dumps(a))
os.kill(pid,signal.SIGCONT)
