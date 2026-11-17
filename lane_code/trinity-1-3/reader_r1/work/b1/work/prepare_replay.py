from pathlib import Path
W=Path.cwd();d=W/'work/replay';d.mkdir(exist_ok=True)
for p in (W/'in/replay').iterdir():
 if p.name.endswith('.py') or p.name.startswith('replay_'):continue
 (d/p.name).symlink_to(p)
s=(W/'in/replay/replay2.py').read_text()
s=s.replace("sys.path[:0] = ['f3/p446/b', 'f3/p446/tree']",f"sys.path[:0] = [{str(W/'work/p/b')!r}, {str(W/'work/p/tree')!r}]")
s=s.replace("sys.path.insert(0, 'f3/p446/b/heads/selector')",f"sys.path.insert(0, {str(W/'work/p/b/heads/selector')!r})")
a=s.index('class Select:');b=s.index('def run(job):',a);s=s[:a]+s[b:]
s=s.replace("        sel = Select(rule)\n        st = S1.StageOne(detect, HEAD, geom)\n        sock = GR.StageOneSocket(st.propose, sel, (240, 320), 32)","        st = S1.StageOne(detect, HEAD, geom, rule=rule)\n        sock = GR.StageOneSocket(st.propose, st.select, (240, 320), 32)")
s=s.replace("sel=sel.log, queries=sock.queries","stage1=st.diagnostics, queries=sock.queries")
s=s.replace("        out = {}", "        from e2e_reader.servers import ReadServers\n        servers = ReadServers(geom, sess)\n        out = {}; info = {}")
s=s.replace("out[n] = sess.execute('<ground obj=\"%s\" mode=\"box\">' % n)","out[n], info[n] = servers.session_call('<ground obj=\"%s\" mode=\"box\">' % n)\n            assert len(json.dumps(info[n]['stage1'], allow_nan=False).encode()) < 64 * 1024")
s=s.replace("gap = sess.execute(gap_call) if gap_call else None", "gap = servers.session_call(gap_call)[0] if gap_call else None")
(d/'replay_patched.py').write_text(s)
