"""Gated deterministic tar writer: stops itself before any payload IO, then streams a USTAR tar of a
file list ([source, member] pairs) to stdout with mtime 0, uid/gid 0, mode 0644. Never execs or retries."""
import json, os, signal, sys, tarfile
os.kill(os.getpid(), signal.SIGSTOP)
pairs = json.load(open(sys.argv[1]))
out = sys.stdout.buffer
with tarfile.open(fileobj=out, mode='w|', format=tarfile.USTAR_FORMAT) as tar:
    for src, member in pairs:
        st = os.stat(src)
        info = tarfile.TarInfo(member); info.size = st.st_size; info.mode = 0o644; info.mtime = 0
        info.uid = info.gid = 0; info.uname = info.gname = ''
        with open(src, 'rb') as f:
            tar.addfile(info, f)
out.flush()
